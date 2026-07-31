# ═════════════════════════════════════════════════════════════════════════
#  Key: C major   |   Tempo: 150 BPM   |   ~6s triumphant "You Win!" sting
# ═════════════════════════════════════════════════════════════════════════

_BEAT = 60.0 / 150.0  # quarter note
_H = _BEAT * 2  # half note
_Q = _BEAT  # quarter
_E = _BEAT / 2  # eighth
_W = _BEAT * 4  # whole note — the final held note

# ── MELODY (Pulse 1) ────────────────────────────────────────────────────
# Call (ascending triad stab) -> descending flourish -> finale (held tonic)

MELODY = [
    # Call
    ("Do5", _E),
    ("Mi5", _E),
    ("Sol5", _E),
    ("Do6", _E),
    ("Mi6", _Q),
    ("Do6", _H),
    # Descending flourish
    ("Si5", _E),
    ("La5", _E),
    ("Sol5", _E),
    ("Fa5", _E),
    ("Mi5", _E),
    ("Re5", _E),
    ("Do5", _Q),
    # Finale
    ("Sol5", _E),
    ("Do6", _E),
    ("Mi6", _Q),
    ("Sol5", _E),
    ("Do6", _W),  # held triumphant final note
]

# ── CHORD ROOTS  (pad, held under each phrase) ──────────────────────────

CHORDS = [
    ("Do3", 2.0),  # tonic pedal under the call
    ("Sol3", 1.6),  # dominant pedal under the descending flourish
    ("Do3", 2.6),  # tonic pedal under the finale
]

# ── BASS  (triangle channel, an octave below the pad) ───────────────────

BASS = [
    ("Do2", 2.0),
    ("Sol2", 1.6),
    ("Do2", 2.6),
]

# ── PERCUSSION  (8th-note pattern — staccato stabs, silent under sustain) ─
# (True = noise hit, False = rest)

PERC = (
    [(True, _E)] * 4
    + [(False, _E)] * 6
    + [(True, _E), (False, _E), (True, _E), (False, _E), (True, _E)]
    + [(False, _E)] * 3
    + [(True, _E), (True, _E), (False, _E), (False, _E), (True, _E)]
    + [(False, _E)] * 8
)
