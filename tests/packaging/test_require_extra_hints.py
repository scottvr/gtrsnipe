"""Contract for the graceful-degradation helper `_require_extra`.

CLI callers get a clean SystemExit(1) (no traceback); library callers get an
ImportError. Both carry the `pip install 'gtrsnipe[<extra>]'` hint.
"""
import pytest

from gtrsnipe.converter import _require_extra


def test_cli_mode_raises_systemexit_with_hint():
    with pytest.raises(SystemExit) as exc:
        _require_extra("audio", "audio input transcription", cli=True)
    assert exc.value.code == 1


def test_library_mode_raises_importerror_with_hint():
    with pytest.raises(ImportError) as exc:
        _require_extra("separation", "stem isolation (demucs)", cli=False)
    msg = str(exc.value)
    assert "pip install 'gtrsnipe[separation]'" in msg


def test_hint_names_the_requested_extra():
    with pytest.raises(ImportError) as exc:
        _require_extra("audio", "noise reduction", cli=False)
    assert "gtrsnipe[audio]" in str(exc.value)
