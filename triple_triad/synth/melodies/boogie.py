# ═════════════════════════════════════════════════════════════════════════
#  Key: F major   |   Tempo: 96 BPM   |   12-bar boogie blues (30 s)
# ═════════════════════════════════════════════════════════════════════════
# Standard 12-bar blues form (I-I-I-I-IV-IV-I-I-V-IV-I-V) with a
# walking-sixths boogie-woogie bass line under a syncopated riff melody.

_BEAT = 60.0 / 96.0  # quarter note
_H = _BEAT * 2  # half note
_Q = _BEAT  # quarter
_E = _BEAT / 2  # eighth
_S = _BEAT / 4  # sixteenth
_BAR = _Q * 4  # one 4/4 bar (2.5 s at this tempo)

# ── MELODY (Pulse 1) ─────────────────────────────────────────────────────
# Syncopated riffs over each chord, closing with a blue-note (b7) run.

_RIFF_I_A = [("Fa4", _E), ("La4", _E), ("Do5", _Q), ("La4", _E), ("Fa4", _E), ("R", _Q)]
_RIFF_I_B = [
    ("Sol4", _E),
    ("La4", _E),
    ("Do5", _Q),
    ("Re5", _E),
    ("Do5", _E),
    ("La4", _Q),
]
_RIFF_IV_A = [
    ("Sib4", _E),
    ("Re5", _E),
    ("Fa5", _Q),
    ("Re5", _E),
    ("Sib4", _E),
    ("R", _Q),
]
_RIFF_IV_B = [
    ("Do5", _E),
    ("Re5", _E),
    ("Fa5", _Q),
    ("Sol5", _E),
    ("Fa5", _E),
    ("Re5", _Q),
]
_RIFF_V = [("Do5", _E), ("Mi5", _E), ("Sol5", _Q), ("Mi5", _E), ("Do5", _E), ("R", _Q)]
_BLUES_RUN = [
    ("Fa5", _S),
    ("Mib5", _S),
    ("Do5", _S),
    ("La4", _S),
    ("Fa4", _Q),
    ("R", _H),
]
_TURNAROUND_HOLD = [("Do5", _H), ("R", _H)]

MELODY = (
    _RIFF_I_A
    + _RIFF_I_B  # bars 1-2 (I)
    + _RIFF_I_A
    + _RIFF_I_B  # bars 3-4 (I)
    + _RIFF_IV_A
    + _RIFF_IV_B  # bars 5-6 (IV)
    + _RIFF_I_A
    + _RIFF_I_B  # bars 7-8 (I)
    + _RIFF_V  # bar 9 (V)
    + _RIFF_IV_A  # bar 10 (IV)
    + _BLUES_RUN  # bar 11 (I) — blue-note run
    + _TURNAROUND_HOLD  # bar 12 (V) — held, ready to loop
)

# ── CHORD ROOTS  (one root per bar, pad channel) ────────────────────────

CHORDS = [
    ("Fa3", _BAR),
    ("Fa3", _BAR),
    ("Fa3", _BAR),
    ("Fa3", _BAR),  # I
    ("Sib3", _BAR),
    ("Sib3", _BAR),  # IV
    ("Fa3", _BAR),
    ("Fa3", _BAR),  # I
    ("Do4", _BAR),  # V
    ("Sib3", _BAR),  # IV
    ("Fa3", _BAR),  # I
    ("Do4", _BAR),  # V (turnaround)
]

# ── BASS  (triangle channel — walking root-3rd-5th-6th boogie pattern) ──

_WALK_I = [
    ("Fa2", _E),
    ("La2", _E),
    ("Do3", _E),
    ("Re3", _E),
    ("Do3", _E),
    ("La2", _E),
    ("Fa2", _E),
    ("La2", _E),
]
_WALK_IV = [
    ("Sib2", _E),
    ("Re3", _E),
    ("Fa3", _E),
    ("Sol3", _E),
    ("Fa3", _E),
    ("Re3", _E),
    ("Sib2", _E),
    ("Re3", _E),
]
_WALK_V = [
    ("Do3", _E),
    ("Mi3", _E),
    ("Sol3", _E),
    ("La3", _E),
    ("Sol3", _E),
    ("Mi3", _E),
    ("Do3", _E),
    ("Mi3", _E),
]

BASS = (
    _WALK_I * 4  # bars 1-4 (I)
    + _WALK_IV * 2  # bars 5-6 (IV)
    + _WALK_I * 2  # bars 7-8 (I)
    + _WALK_V  # bar 9 (V)
    + _WALK_IV  # bar 10 (IV)
    + _WALK_I  # bar 11 (I)
    + _WALK_V  # bar 12 (V)
)

# ── PERCUSSION  (steady backbeat on 2 and 4, driving the shuffle) ──────
# (True = noise hit, False = rest)

_BACKBEAT = [
    (False, _E),
    (False, _E),
    (True, _E),
    (False, _E),
    (False, _E),
    (False, _E),
    (True, _E),
    (False, _E),
]

PERC = _BACKBEAT * 12
