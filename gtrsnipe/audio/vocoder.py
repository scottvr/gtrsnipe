import torch
import json
import os
from .models.hifi_GAN.env import AttrDict
from .models.hifi_GAN.models import Generator

# We'll assume the user places the hifi-gan repo code in a sub-folder
# and the downloaded universal model in gtrsnipe/models/

HIFI_GAN_CONFIG_PATH = "./models/hifi_gan/config.json"
HIFI_GAN_CHECKPOINT_PATH = "./models/hifi_gan/g_02500000"

class HiFiGanVocoder:
    def __init__(self, device='cpu'):
        with open(HIFI_GAN_CONFIG_PATH) as f:
            data = f.read()
        json_config = json.loads(data)
        self.h = AttrDict(json_config)
        
        self.device = torch.device(device)
        
        self.generator = Generator(self.h).to(self.device)
        state_dict_g = self._load_checkpoint(HIFI_GAN_CHECKPOINT_PATH, self.device)
        self.generator.load_state_dict(state_dict_g['generator'])
        self.generator.eval()
        self.generator.remove_weight_norm()

    def _load_checkpoint(self, filepath, device):
        assert os.path.isfile(filepath)
        checkpoint_dict = torch.load(filepath, map_location=device)
        return checkpoint_dict

    @torch.no_grad()
    def synthesize_waveform(self, mel_spectrogram):
        """
        Takes a Mel spectrogram and synthesizes a waveform.
        
        Args:
            mel_spectrogram (Tensor): A Mel spectrogram of shape [1, 80, T]
        
        Returns:
            Tensor: The synthesized audio waveform.
        """
        MAX_WAV_VALUE = 32768.0
        
        y_g_hat = self.generator(mel_spectrogram)
        audio = y_g_hat.squeeze()
        audio = audio * MAX_WAV_VALUE
        return audio.cpu().numpy().ast.modelsype('int16').models