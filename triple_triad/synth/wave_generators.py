import numpy as np

from .constants import SAMPLE_RATE, NOTE_FREQ, HARMONY_MAP
from .melodies.background_music import CHORDS, MELODY, BASS, PERC

def _square(frequency: float, duration: float, duty: float = 0.5) -> np.ndarray:
    """pulse channel (square wave)."""
    if frequency == 0:
        return np.zeros(int(duration * SAMPLE_RATE))
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    return np.sign(np.sin(2 * np.pi * frequency * t) + (2 * duty - 1))


def _triangle(frequency: float, duration: float) -> np.ndarray:
    """triangle channel (bass)."""
    if frequency == 0:
        return np.zeros(int(duration * SAMPLE_RATE))
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    return 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1


def _noise(duration: float) -> np.ndarray:
    """noise channel (percussion)."""
    return np.random.uniform(-1, 1, int(duration * SAMPLE_RATE))


def _envelope(
    wave: np.ndarray,
    attack: float = 0.01,
    decay: float = 0.1,
    sustain_level: float = 0.7,
    release: float = 0.1,
) -> np.ndarray:
    """ADSR envelope."""
    total = len(wave)
    a = int(attack * SAMPLE_RATE)
    d = int(decay * SAMPLE_RATE)
    r = int(release * SAMPLE_RATE)
    s = total - a - d - r
    if s < 0:
        return wave * np.linspace(1, 0, total)
    env = np.concatenate(
        [
            np.linspace(0, 1, a),
            np.linspace(1, sustain_level, d),
            np.full(s, sustain_level),
            np.linspace(sustain_level, 0, r),
        ]
    )
    return wave * env


def _render_notes(notes, wave_fn, vol, **env):
    """Render a list of (note, duration) → float64 buffer × volume."""
    buf = np.array([], dtype=np.float64)
    for note, dur in notes:
        freq = NOTE_FREQ.get(note, 0)
        w = wave_fn(freq, dur)
        w = _envelope(w, **env)
        buf = np.concatenate([buf, w])
    return buf * vol


def _render_melody(notes):
    return _render_notes(
        notes, _square, 0.30, attack=0.02, decay=0.15, sustain_level=0.55, release=0.15
    )


def _render_harmony(melody_notes):
    """Generate a diatonic-third harmony from the melody."""
    h_notes = []
    for note, dur in melody_notes:
        if note == "R":
            h_notes.append(("R", dur))
            continue
        nb, octv = note[:-1], int(note[-1])
        hn = HARMONY_MAP.get(nb, "Do")
        # La→Do and Si→Re cross into the next octave
        if nb in ("La", "Si", "Sib"):
            octv += 1
        h_notes.append((f"{hn}{octv}", dur))
    return _render_notes(
        h_notes,
        _square,
        0.18,
        attack=0.03,
        decay=0.15,
        sustain_level=0.35,
        release=0.15,
    )


def _render_pad(chord_notes):
    """Soft sustained pad (slow attack, long release)."""
    return _render_notes(
        chord_notes,
        _square,
        0.10,
        attack=0.15,
        decay=0.3,
        sustain_level=0.5,
        release=0.4,
    )


def _render_bass(bass_notes):
    return _render_notes(
        bass_notes,
        _triangle,
        0.25,
        attack=0.02,
        decay=0.15,
        sustain_level=0.75,
        release=0.1,
    )


def _render_perc(perc_pattern):
    buf = np.array([], dtype=np.float64)
    for hit, dur in perc_pattern:
        if hit:
            w = _noise(dur)
            w = _envelope(w, attack=0.001, decay=0.04, sustain_level=0.20, release=0.04)
        else:
            w = np.zeros(int(dur * SAMPLE_RATE))
        buf = np.concatenate([buf, w])
    return buf * 0.10


def generate_music_buffer() -> np.ndarray:
    """Mix all five channels into one float64 buffer."""
    melody = _render_melody(MELODY)
    harmony = _render_harmony(MELODY)
    pad = _render_pad(CHORDS)
    bass = _render_bass(BASS)
    perc = _render_perc(PERC)

    # Trim all to shortest channel
    length = min(len(melody), len(harmony), len(pad), len(bass), len(perc))
    mixed = (
        melody[:length] * 1.0
        + harmony[:length] * 1.0
        + pad[:length] * 1.0
        + bass[:length] * 1.0
        + perc[:length] * 1.0
    )

    # Normalize to ±0.8
    peak = np.max(np.abs(mixed))
    if peak > 0:
        mixed = mixed / peak * 0.8
    return mixed
