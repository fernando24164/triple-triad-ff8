# Triple-triad

A terminal-based Python implementation of the classic **Triple Triad** card game from *Final Fantasy VIII*, complete with chiptune background music, smart AI opponents, and support for official rules like Same, Plus, and Open.

---

## ✨ Features

- **Authentic gameplay** — 110 cards from FFVIII
- **3 difficulty levels** — Easy, Medium, and Hard CPU opponents with distinct AI strategies
- **Optional rules** — Open, Same, Plus, and Random capture mechanics
- **Chiptune music** — Retro-style background music generated with NumPy and played through Pygame
- **Interactive deck builder** — Browse, filter, and sort all cards before picking your hand
- **Deck presets** — Themed decks (Fire Power, Ice Wall, Thunder Rush, and more)
- **Terminal rendering** — ANSI-colored board with card ownership indicators

---

## 🎮 How to Play

Triple Triad is a 2-player card game played on a 3×3 grid. Each player has 5 cards. Players take turns placing one card on the board. When a card is placed adjacent to an opponent's card, the touching sides are compared — if the attacker's value is higher, the defender's card is captured. The player with the most cards on the board at the end wins.

```
 ┌──────────────────┬──────────────────┬──────────────────┐
 │                  │                  │                  │
 │     [ 1 ]        │     [ 2 ]        │     [ 3 ]        │
 │                  │                  │                  │
 ├──────────────────┼──────────────────┼──────────────────┤
 │ ■Ifrit           │                  │                  │
 │      ▲ 9         │     [ 5 ]        │     [ 6 ]        │
 │ ◀ 5   Ice   8 ▶  │                  │                  │
 │      ▼ 6         │                  │                  │
 ├──────────────────┼──────────────────┼──────────────────┤
 │ □Shiva           │                  │                  │
 │      ▲ 6         │     [ 8 ]        │     [ 9 ]        │
 │ ◀ 6   Ice   9 ▶  │                  │                  │
 │      ▼ 7         │                  │                  │
 └──────────────────┴──────────────────┴──────────────────┘
```

- **■** = Your card
- **□** = CPU's card
- Numbers inside empty cells = board position (1–9)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+**
- **NumPy** (for audio synthesis)
- **Pygame** (for audio playback — optional, game runs silently without it)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/triple-triad.git
cd triple-triad

# Install dependencies
uv sync --locked
```

### Run the Game

```bash
python -m triple_triad.game
```

---

## 📦 Project Structure

```
triple_triad/
├── data/
│   └── cards.py          # All 110 card definitions with stats & elements
├── synth/
│   ├── melodies/
│   │   └── background_music.py   # Melody, chords, bass & percussion data
│   ├── constants.py              # Note frequencies and sample rate
│   ├── player.py                 # Threaded chiptune player (pygame)
│   └── wave_generators.py        # Square, triangle & noise wave synthesis
├── ai.py                 # CPU decision-making (random / greedy)
├── board.py              # 3×3 grid state + ANSI terminal renderer
├── cards.py              # Card class with immutable stats via CardStats
├── deck.py               # Deck builders, presets & interactive picker
├── game.py               # Main game loop and orchestration
├── rules.py              # Capture logic (basic, Same, Plus)
└── ui.py                 # Display helpers and rule selection menu
```


## 🎵 Audio

The game includes a built-in chiptune soundtrack synthesized entirely in software:

- **5 channels**: melody, harmony, pad, bass, and percussion
- **Generated with NumPy** — no audio files required
- **Played through Pygame** — if Pygame is unavailable, the game runs silently

---

## 🧩 Rules

| Rule | Description |
|------|-------------|
| **Open** | CPU's hand is visible to the player |
| **Same** | If 2+ adjacent cards share equal values, all are captured |
| **Plus** | If 2+ adjacent cards share equal value *sums*, all are captured |
| **Random** | Cards are dealt randomly from the full pool |

---

## 🛠 Development

### Install Dev Dependencies

```bash
uv sync --locked
```

### Run Tests

```bash
pytest
```

### Lint

```bash
ruff check .
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create a feature branch** — `git checkout -b feature/my-feature`
3. **Make your changes** — follow the existing code style
4. **Run tests** — `pytest`
5. **Submit a pull request**

Please open an issue first for major changes to discuss the approach.

---

## Build

```sh
uv build
```

```sh
twine upload dist/*
```

## 📄 License

This project is for educational and personal use. Triple Triad is a minigame from *Final Fantasy VIII*, © Square Enix. All card names and game mechanics are the property of their respective owners.

---

## 🙏 Acknowledgments

- **Square Enix** — for creating Triple Triad in *Final Fantasy VIII*
- The original card stats and element system are faithfully reproduced from the game