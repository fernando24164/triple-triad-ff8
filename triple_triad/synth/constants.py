
SAMPLE_RATE = 44100 # CD quality

# Note frequencies (La = 440Hz) - European solfège system
NOTE_FREQ = {
    "Do2": 65.41,
    "Re2": 73.42,
    "Mi2": 82.41,
    "Fa2": 87.31,
    "Sol2": 98.00,
    "La2": 110.00,
    "Si2": 123.47,
    "Do3": 130.81,
    "Re3": 146.83,
    "Mi3": 164.81,
    "Fa3": 174.61,
    "Sol3": 196.00,
    "La3": 220.00,
    "Si3": 246.94,
    "Do4": 261.63,
    "Re4": 293.66,
    "Mi4": 329.63,
    "Fa4": 349.23,
    "Sol4": 392.00,
    "La4": 440.00,
    "Si4": 493.88,
    "Do5": 523.25,
    "Re5": 587.33,
    "Mi5": 659.25,
    "Fa5": 698.46,
    "Sol5": 783.99,
    "La5": 880.00,
    "Si5": 987.77,
    "Do6": 1046.50,
    "Re6": 1174.66,
    "Mi6": 1318.51,
    "Fa6": 1396.91,
    "Sib2": 116.54,
    "Sib3": 233.08,
    "Sib4": 466.16,
    "R": 0,
}

# Harmonic interval for harmony channel (up a diatonic third in F major)
HARMONY_MAP = {
    "Do": "Mi",
    "Re": "Fa",
    "Mi": "Sol",
    "Fa": "La",
    "Sol": "Si",
    "La": "Do",
    "Si": "Re",
    "Sib": "Re",
}