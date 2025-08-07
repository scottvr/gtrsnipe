import logging
from pathlib import Path
import torch
import torchaudio
from torch.nn import functional as F
from typing import TypedDict, List, Tuple
import onnxruntime as ort
import numpy as np
import json
import os
from .models.hifi_GAN.models import Generator
from .models.hifi_GAN.env import AttrDict
from .models.hifi_GAN.meldataset import mel_spectrogram
from scipy.io.wavfile import write

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent.resolve()
DENOISER_MODEL_PATH = SCRIPT_DIR / "models/denoiser/denoiser_model.onnx"
HIFI_GAN_CONFIG_PATH = SCRIPT_DIR / "models/hifi_GAN/config.json"
HIFI_GAN_CHECKPOINT_PATH = SCRIPT_DIR / "models/hifi_GAN/g_02500000"

class HiFiGanConfig(TypedDict):
    resblock: str
    num_gpus: int
    batch_size: int
    learning_rate: float
    adam_b1: float
    adam_b2: float
    lr_decay: float
    seed: int
    upsample_rates: List[int]
    upsample_kernel_sizes: List[int]
    upsample_initial_channel: int
    resblock_kernel_sizes: List[int]
    resblock_dilation_sizes: List[List[int]]
    n_fft: int
    num_mels: int
    sampling_rate: int
    hop_size: int
    win_size: int
    fmin: int
    fmax: int
    fmax_for_loss: int | None
    num_workers: int
    dist_config: dict

class HiFiGanVocoder:
    def __init__(self, device='cpu'):
        with open(HIFI_GAN_CONFIG_PATH) as f:
            config_dict: HiFiGanConfig = json.load(f)

        self.h = config_dict
        
        h_for_generator = AttrDict(self.h)
        
        self.device = torch.device(device)
        
        self.generator = Generator(h_for_generator).to(self.device)
        
        state_dict_g = self._load_checkpoint(filepath=HIFI_GAN_CHECKPOINT_PATH, device=self.device)
        self.generator.load_state_dict(state_dict_g['generator'])
        self.generator.eval()
        self.generator.remove_weight_norm()
        
        logger.info("HiFi-GAN Vocoder initialized.")
    
    def _load_checkpoint(self, filepath, device):
        assert os.path.isfile(filepath)
        return torch.load(filepath, map_location=device)
    
    @torch.no_grad()
    def synthesize_from_tensor(self, audio_tensor: torch.Tensor, input_sr: int, output_dir: Path) -> str:
        logger.info("[Stage 2/2] Re-synthesizing with HiFi-GAN Vocoder...")
        
        wav = audio_tensor
        # Resample if the denoiser's sample rate differs from HiFi-GAN's
        if input_sr != self.h['sampling_rate']:
            resampler = torchaudio.transforms.Resample(orig_freq=input_sr, new_freq=self.h['sampling_rate'])
            wav = resampler(wav)
        
        # The denoiser output is already [-1, 1], so no need to divide by MAX_WAV_VALUE
        wav = torch.FloatTensor(wav).to(self.device)

        x = mel_spectrogram(wav, self.h['n_fft'], self.h['num_mels'], self.h['sampling_rate'], 
                            self.h['hop_size'], self.h['win_size'], self.h['fmin'], self.h['fmax'])
        
        x = x.to(self.device)
        
        y_g_hat = self.generator(x)
        audio = y_g_hat.squeeze()
        audio = audio * 32768.0
        audio = audio.cpu().numpy().astype('int16')

        # Create a unique output path in the specified directory
        output_path = output_dir / "audio_resynthesized.wav"
        write(str(output_path), self.h['sampling_rate'], audio)

        logger.info(f"--- Resynthesized audio saved to: {output_path} ---")
        return str(output_path)
    

    @torch.no_grad()
    def synthesize_from_audio_file(self, audio_file: str) -> str:
        """Takes a file path, creates a mel spectrogram, and synthesizes a new waveform."""
        logger.info("[Stage 2/2] Re-synthesizing with HiFi-GAN Vocoder...")

        wav, sr = torchaudio.load(audio_file)
        
        if sr != self.h['sampling_rate']:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=self.h['sampling_rate'])
            wav = resampler(wav)
        
        if wav.shape[0] > 1:
            wav = torch.mean(wav, dim=0, keepdim=True)

        MAX_WAV_VALUE = 32768.0
        wav = wav / MAX_WAV_VALUE
        
        # --- THE FIX ---
        # Keep the waveform tensor on the CPU for the mel_spectrogram function.
        wav = torch.FloatTensor(wav)

        # 1. Create the spectrogram on the CPU.
        x = mel_spectrogram(wav, self.h['n_fft'], self.h['num_mels'], self.h['sampling_rate'], 
                            self.h['hop_size'], self.h['win_size'], self.h['fmin'], self.h['fmax'])
        
        # 2. Now, move the resulting spectrogram to the target device (GPU/CPU).
        x = x.to(self.device)

        # 3. Synthesize new audio from the spectrogram.
        y_g_hat = self.generator(x)
        audio = y_g_hat.squeeze()
        audio = audio * MAX_WAV_VALUE
        audio = audio.cpu().numpy().astype('int16')

        p = Path(audio_file)
        output_path = p.with_name(f"{p.stem}_resynthesized.wav")
        write(str(output_path), self.h['sampling_rate'], audio)

        logger.info(f"--- Resynthesized audio saved to: {output_path} ---")
        return str(output_path)

def _run_denoiser(audio_file: str) -> Tuple[torch.Tensor | None, int | None]:
    logger.info("[Stage 1/2] Applying ONNX denoiser...")
    HOP_SIZE, FFT_SIZE, DENOISER_SR = 480, 960, 48000

    try:
        sess_options = ort.SessionOptions()
        ort_session = ort.InferenceSession(DENOISER_MODEL_PATH, sess_options, providers=["CPUExecutionProvider"])
    except Exception as e:
        logger.error(f"Failed to load ONNX model at '{DENOISER_MODEL_PATH}'. Error: {e}")
        return None, None

    ort_session = ort.InferenceSession(str(DENOISER_MODEL_PATH), providers=["CPUExecutionProvider"]) 
    input_audio, sr = torchaudio.load(audio_file)
    if sr != DENOISER_SR:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=DENOISER_SR)
        input_audio = resampler(input_audio)

    input_audio = torch.mean(input_audio, dim=0, keepdim=True).squeeze(0)
    orig_len = input_audio.shape[0]

    padding_size = (HOP_SIZE - orig_len % HOP_SIZE) % HOP_SIZE
    input_audio = F.pad(input_audio, (0, FFT_SIZE + padding_size))
    
    chunked_audio = torch.split(input_audio.squeeze(0), HOP_SIZE)
    state = np.zeros(45304, dtype=np.float32)
    atten_lim_db = np.zeros(1, dtype=np.float32)
    enhanced_chunks = []
    
    for frame in chunked_audio:
        ort_inputs = {"input_frame": frame.numpy(), "states": state, "atten_lim_db": atten_lim_db}
        out = ort_session.run(None, input_feed=ort_inputs)
        enhanced_chunks.append(torch.tensor(out[0]))
        state = out[1]

    enhanced_audio = torch.cat(enhanced_chunks).unsqueeze(0)
    delay = FFT_SIZE - HOP_SIZE
    enhanced_audio = enhanced_audio[:, delay : orig_len + delay]

    logger.info(f"--- Denoising complete. Passing audio tensor in memory. ---")
    # Return the tensor and its sample rate instead of saving to a file
    return enhanced_audio, DENOISER_SR

    
def remove_distortion_effects(audio_file: str) -> str:
    """Applies a two-stage process to remove distortion from an audio file."""
    # Stage 1: Get the clean audio tensor and its sample rate
    denoised_tensor, denoised_sr = _run_denoiser(audio_file)
    
    if denoised_tensor is None or denoised_sr is None:
        logger.error("Denoising failed. Skipping distortion removal.")
        return audio_file # Return the original file to continue the pipeline

    # Stage 2: Initialize the vocoder and synthesize from the in-memory tensor
    vocoder = HiFiGanVocoder()
    output_dir = Path(audio_file).parent
    final_file = vocoder.synthesize_from_tensor(denoised_tensor, denoised_sr, output_dir)
    
    return final_file