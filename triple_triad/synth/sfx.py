import os

import numpy as np
import pygame

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from .constants import SAMPLE_RATE

try:
    import numpy as np
    import pygame

    HAS_AUDIO = True
except (ImportError, OSError):
    HAS_AUDIO = False


def _square_wave(frequency: float, duration: float, duty: float = 0.5) -> np.ndarray:
    if frequency == 0:
        return np.zeros(int(duration * SAMPLE_RATE))
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    result: np.ndarray = np.sign(np.sin(2 * np.pi * frequency * t) + (2 * duty - 1))
    return result


def _envelope(
    wave: np.ndarray,
    attack: float = 0.001,
    decay: float = 0.05,
    sustain_level: float = 0.0,
    release: float = 0.05,
) -> np.ndarray:
    total = len(wave)
    a = int(attack * SAMPLE_RATE)
    d = int(decay * SAMPLE_RATE)
    r = int(release * SAMPLE_RATE)
    s = total - a - d - r
    if s < 0:
        env1: np.ndarray = np.linspace(1, 0, total)
        out1: np.ndarray = wave * env1
        return out1
    env = np.concatenate(
        [
            np.linspace(0, 1, a),
            np.linspace(1, sustain_level, d),
            np.full(s, sustain_level),
            np.linspace(sustain_level, 0, r),
        ]
    )
    out: np.ndarray = wave * env
    return out


def _generate_sfx(
    notes: list[tuple[float, float]],
    vol: float = 0.5,
    duty: float = 0.5,
    attack: float = 0.001,
    decay: float = 0.03,
    release: float = 0.03,
) -> np.ndarray:
    buf = np.array([], dtype=np.float64)
    for freq, dur in notes:
        w = _square_wave(freq, dur, duty)
        w = _envelope(w, attack=attack, decay=decay, release=release)
        buf = np.concatenate([buf, w])
    return buf * vol


def _make_stereo(mono: np.ndarray) -> np.ndarray:
    pcm = (mono * 32767).astype(np.int16)
    return np.column_stack((pcm, pcm))


def _play_buffer(buf: np.ndarray) -> None:
    if not HAS_AUDIO:
        return
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(
                frequency=SAMPLE_RATE,
                size=-16,
                channels=2,
                buffer=512,
            )
        stereo = _make_stereo(buf)
        sound = pygame.sndarray.make_sound(stereo)
        sound.play()
    except Exception:
        pass


def play_cursor() -> None:
    buf = _generate_sfx(
        [(1046.5, 0.05)], vol=0.18, attack=0.001, decay=0.03, release=0.02
    )
    _play_buffer(buf)


def play_confirm() -> None:
    buf = _generate_sfx(
        [(1046.5, 0.08), (784.0, 0.10)],
        vol=0.25,
        attack=0.002,
        decay=0.06,
        release=0.04,
    )
    _play_buffer(buf)


def play_cancel() -> None:
    buf = _generate_sfx(
        [(392.0, 0.07), (349.2, 0.07)],
        vol=0.14,
        attack=0.002,
        decay=0.04,
        release=0.03,
    )
    _play_buffer(buf)


def play_error() -> None:
    buf = _generate_sfx(
        [(196.0, 0.15)], vol=0.18, duty=0.3, attack=0.005, decay=0.08, release=0.05
    )
    _play_buffer(buf)
