# ═════════════════════════════════════════════════════════════════════════
#  Key: A minor   |   Tempo: 80 BPM   |   ~3.75s somber "Game Over" sting
# ═════════════════════════════════════════════════════════════════════════

_BEAT = 60.0 / 80.0  # quarter note
_H = _BEAT * 2  # half note
_Q = _BEAT  # quarter

# ── MELODY (Pulse 1) ────────────────────────────────────────────────────
# Descending 5-4-3-1 lament line, resolving on the tonic.

MELODY = [
    ("Mi5", _Q),
    ("Re5", _Q),
    ("Do5", _Q),
    ("La4", _H),  # held tonic — the resigned resolution
]

# ── CHORD ROOT  (pad, a single somber drone under the whole phrase) ─────

CHORDS = [
    ("La3", _Q * 3 + _H),
]

# ── BASS  (triangle channel, an octave below the pad) ───────────────────

BASS = [
    ("La2", _Q * 3 + _H),
]
