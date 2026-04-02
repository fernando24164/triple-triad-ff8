# ═════════════════════════════════════════════════════════════════════════
#  Key: F major   |   Tempo: 108 BPM
# ═════════════════════════════════════════════════════════════════════════

_BEAT = 60.0 / 108.0  # quarter note
_H = _BEAT * 2  # half note
_Q = _BEAT  # quarter
_E = _BEAT / 2  # eighth

# ── MELODY (Pulse 1) ────────────────────────────────────────────────────
# 4-bar intro  +  8-bar A  +  8-bar B  =  20 bars  (≈ 44 s)

MELODY = [
    # ── Intro (gentle, no rhythm) ──────────────────────────────────────
    # Bar 1
    ("R", _H),
    ("Fa4", _Q),
    ("Sol4", _Q),
    # Bar 2
    ("La4", _Q),
    ("Do5", _Q),
    ("La4", _H),
    # Bar 3
    ("Sol4", _Q),
    ("Fa4", _Q),
    ("Sol4", _Q),
    ("La4", _Q),
    # Bar 4
    ("Fa4", _H),
    ("R", _H),
    # ── A section  (the iconic soaring phrase) ─────────────────────────
    # Bar 5
    ("Fa4", _Q),
    ("La4", _Q),
    ("Do5", _Q),
    ("Fa5", _Q),
    # Bar 6
    ("Mi5", _H),
    ("Re5", _Q),
    ("Do5", _Q),
    # Bar 7
    ("La4", _Q),
    ("Sol4", _Q),
    ("La4", _Q),
    ("Do5", _Q),
    # Bar 8
    ("La4", _H),  # held resolve
    # Bar 9
    ("Sib4", _Q),
    ("La4", _Q),
    ("Sol4", _Q),
    ("La4", _Q),
    # Bar 10
    ("Sol4", _Q),
    ("Fa4", _Q),
    ("Sol4", _H),
    # Bar 11
    ("La4", _Q),
    ("Do5", _Q),
    ("Re5", _Q),
    ("Do5", _Q),
    # Bar 12
    ("La4", _H),  # held resolve
    # ── B section  (gentle descending counter-melody) ──────────────────
    # Bar 13
    ("Fa5", _Q),
    ("Mi5", _Q),
    ("Re5", _Q),
    ("Do5", _Q),
    # Bar 14
    ("Re5", _Q),
    ("Do5", _Q),
    ("La4", _H),
    # Bar 15
    ("Sol4", _Q),
    ("Fa4", _Q),
    ("Sol4", _Q),
    ("La4", _Q),
    # Bar 16
    ("Sib4", _Q),
    ("La4", _Q),
    ("Sol4", _H),
    # Bar 17
    ("Fa4", _Q),
    ("La4", _Q),
    ("Do5", _Q),
    ("Re5", _Q),
    # Bar 18
    ("Do5", _Q),
    ("La4", _Q),
    ("Fa4", _H),
    # Bar 19
    ("Sol4", _Q),
    ("La4", _Q),
    ("Sol4", _Q),
    ("Fa4", _Q),
    # Bar 20
    ("Fa4", _H),
]

# ── CHORD ROOTS  (half-note stride) ─────────────────────────────────────

CHORDS = [
    # Intro — sustained Fa
    ("Fa3", _H),
    ("Fa3", _H),
    ("Fa3", _H),
    ("Fa3", _H),
    # A
    ("Fa3", _H),
    ("Re3", _H),
    ("Sib2", _H),
    ("Fa3", _H),
    ("Sol3", _H),
    ("Fa3", _H),
    ("Re3", _H),
    ("Fa3", _H),
    # B
    ("Re3", _H),
    ("Fa3", _H),
    ("Sol3", _H),
    ("Sib2", _H),
    ("Fa3", _H),
    ("Re3", _H),
    ("Sol3", _H),
    ("Fa3", _H),
]

# ── BASS  (triangle channel — roots + fifths) ──────────────────────────

BASS = [
    ("Fa2", _H),
    ("Fa2", _H),
    ("Fa2", _H),
    ("Fa2", _H),
    ("Fa2", _H),
    ("Re2", _H),
    ("Sib1", _H),
    ("Fa2", _H),
    ("Sol2", _H),
    ("Fa2", _H),
    ("Re2", _H),
    ("Fa2", _H),
    ("Re2", _H),
    ("Fa2", _H),
    ("Sol2", _H),
    ("Sib1", _H),
    ("Fa2", _H),
    ("Re2", _H),
    ("Sol2", _H),
    ("Fa2", _H),
]

# ── PERCUSSION  (8th-note pattern, kicks in at bar 5) ───────────────────
# (True = noise hit, False = rest)

PERC = [
    (False, _E),
    (False, _E),
    (False, _E),
    (False, _E),
    (False, _E),
    (False, _E),
    (False, _E),
    (False, _E),
] + [
    (True, _E),
    (False, _E),
    (False, _E),
    (False, _E),
    (True, _E),
    (False, _E),
    (False, _E),
    (False, _E),
] * 16  # 4 intro bars silent  +  16 A/B bars