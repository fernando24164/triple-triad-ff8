from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict


class Element(str, Enum):
    """Card element types (str enum for backward compatibility)."""
    THUNDER = "Thunder"
    EARTH = "Earth"
    ICE = "Ice"
    WIND = "Wind"
    POISON = "Poison"
    FIRE = "Fire"
    WATER = "Water"
    HOLY = "Holy"


@dataclass(frozen=True)
class CardStats:
    """Immutable card statistics."""
    name: str
    top: int
    right: int
    bottom: int
    left: int
    element: Optional[Element]
    level: int


# Build CARDS dictionary using CardStats
CARDS: Dict[str, CardStats] = {
    # Name: (top, right, bottom, left, element, level)
    "Geezard":      CardStats("Geezard", 1, 4, 1, 5, None, 1),
    "Funguar":      CardStats("Funguar", 5, 1, 1, 3, None, 1),
    "Bite Bug":     CardStats("Bite Bug", 1, 3, 3, 5, None, 1),
    "Red Bat":      CardStats("Red Bat", 6, 1, 1, 2, None, 1),
    "Blobra":       CardStats("Blobra", 2, 3, 1, 5, None, 1),
    "Gayla":        CardStats("Gayla", 2, 4, 4, 1, Element.THUNDER, 2),
    "Gesper":       CardStats("Gesper", 1, 5, 4, 3, None, 2),
    "Fastitocalon": CardStats("Fastitocalon", 3, 1, 5, 4, Element.EARTH, 2),
    "Blood Soul":   CardStats("Blood Soul", 2, 6, 1, 1, None, 2),
    "Caterchipillar":CardStats("Caterchipillar", 4, 3, 2, 6, None, 2),
    "Cockatrice":   CardStats("Cockatrice", 2, 6, 1, 3, Element.THUNDER, 2),
    "Grat":         CardStats("Grat", 7, 1, 1, 3, None, 3),
    "Buel":         CardStats("Buel", 6, 3, 2, 1, None, 3),
    "Mesmerize":    CardStats("Mesmerize", 5, 4, 3, 3, None, 3),
    "Glacial Eye":  CardStats("Glacial Eye", 6, 3, 1, 4, Element.ICE, 3),
    "Belhelmel":    CardStats("Belhelmel", 3, 3, 4, 6, None, 3),
    "Thrustaevis":  CardStats("Thrustaevis", 5, 5, 3, 2, Element.WIND, 3),
    "Anacondaur":   CardStats("Anacondaur", 5, 5, 1, 3, Element.POISON, 3),
    "Creeps":       CardStats("Creeps", 5, 2, 5, 3, Element.THUNDER, 3),
    "Grendel":      CardStats("Grendel", 4, 3, 6, 3, Element.THUNDER, 3),
    "Jelleye":      CardStats("Jelleye", 3, 7, 2, 1, None, 3),
    "Grand Mantis": CardStats("Grand Mantis", 5, 3, 2, 6, None, 3),
    "Forbidden":    CardStats("Forbidden", 6, 2, 6, 3, None, 4),
    "Armadodo":     CardStats("Armadodo", 6, 6, 3, 1, Element.EARTH, 4),
    "Tri-Face":     CardStats("Tri-Face", 3, 5, 5, 5, Element.POISON, 4),
    "Fastitocalon-F":CardStats("Fastitocalon-F", 2, 8, 4, 2, Element.EARTH, 4),
    "Snow Lion":    CardStats("Snow Lion", 7, 3, 1, 5, Element.ICE, 4),
    "Ochu":         CardStats("Ochu", 5, 3, 6, 3, None, 4),
    "SAM08G":       CardStats("SAM08G", 5, 4, 6, 3, Element.FIRE, 4),
    "Death Claw":   CardStats("Death Claw", 4, 2, 4, 8, Element.FIRE, 4),
    "Cactuar":      CardStats("Cactuar", 6, 3, 2, 6, None, 4),
    "Tonberry":     CardStats("Tonberry", 3, 4, 6, 5, None, 4),
    "Abyss Worm":   CardStats("Abyss Worm", 7, 5, 2, 3, Element.EARTH, 4),
    "Turtapod":     CardStats("Turtapod", 2, 7, 3, 6, None, 5),
    "Vysage":       CardStats("Vysage", 6, 5, 5, 5, None, 5),
    "T-Rexaur":     CardStats("T-Rexaur", 4, 7, 6, 2, None, 5),
    "Bomb":         CardStats("Bomb", 2, 3, 7, 6, Element.FIRE, 5),
    "Blitz":        CardStats("Blitz", 1, 7, 6, 4, Element.THUNDER, 5),
    "Wendigo":      CardStats("Wendigo", 7, 6, 1, 3, None, 5),
    "Torama":       CardStats("Torama", 7, 4, 4, 4, None, 5),
    "Imp":          CardStats("Imp", 3, 6, 7, 3, None, 5),
    "Blue Dragon":  CardStats("Blue Dragon", 6, 3, 2, 7, Element.POISON, 5),
    "Adamantoise":  CardStats("Adamantoise", 4, 6, 5, 6, Element.EARTH, 5),
    "Hexadragon":   CardStats("Hexadragon", 7, 3, 5, 4, Element.FIRE, 5),
    "Iron Giant":   CardStats("Iron Giant", 6, 5, 5, 6, None, 6),
    "Behemoth":     CardStats("Behemoth", 3, 7, 6, 5, None, 6),
    "Chimera":      CardStats("Chimera", 7, 3, 6, 5, Element.WATER, 6),
    "PuPu":         CardStats("PuPu", 3, 1, 10, 2, None, 6),
    "Elastoid":     CardStats("Elastoid", 6, 7, 2, 6, None, 6),
    "GIM47N":       CardStats("GIM47N", 4, 7, 6, 5, None, 6),
    "Malboro":      CardStats("Malboro", 7, 2, 7, 4, Element.POISON, 6),
    "Ruby Dragon":  CardStats("Ruby Dragon", 7, 6, 4, 5, Element.FIRE, 6),
    "Elnoyle":      CardStats("Elnoyle", 5, 6, 3, 7, None, 6),
    "Tonberry King":CardStats("Tonberry King", 4, 4, 6, 8, None, 6),
    "Wedge, Biggs": CardStats("Wedge, Biggs", 6, 7, 6, 2, None, 6),
    "Fujin, Raijin":CardStats("Fujin, Raijin", 2, 8, 5, 5, None, 7),
    "Elvoret":      CardStats("Elvoret", 7, 4, 8, 3, Element.WIND, 7),
    "X-ATM092":     CardStats("X-ATM092", 4, 8, 5, 6, None, 7),
    "Granaldo":     CardStats("Granaldo", 7, 5, 2, 8, None, 7),
    "Gerogero":     CardStats("Gerogero", 1, 3, 8, 7, Element.POISON, 7),
    "Iguion":       CardStats("Iguion", 8, 2, 2, 8, None, 7),
    "Abadon":       CardStats("Abadon", 6, 5, 8, 5, None, 7),
    "Trauma":       CardStats("Trauma", 4, 8, 5, 6, None, 7),
    "Oilboyle":     CardStats("Oilboyle", 1, 8, 6, 7, None, 7),
    "Shumi Tribe":  CardStats("Shumi Tribe", 6, 4, 5, 8, None, 7),
    "Krysta":       CardStats("Krysta", 7, 1, 8, 5, None, 7),
    "Propagator":   CardStats("Propagator", 8, 4, 8, 4, None, 8),
    "Jumbo Cactuar":CardStats("Jumbo Cactuar", 8, 4, 4, 8, None, 8),
    "Tri-Point":    CardStats("Tri-Point", 8, 8, 5, 3, Element.THUNDER, 8),
    "Gargantua":    CardStats("Gargantua", 5, 8, 6, 6, None, 8),
    "Mobile Type 8":CardStats("Mobile Type 8", 8, 3, 6, 7, None, 8),
    "Sphinxara":    CardStats("Sphinxara", 8, 3, 8, 5, None, 8),
    "Tiamat":       CardStats("Tiamat", 8, 4, 8, 5, None, 8),
    "BGH251F2":     CardStats("BGH251F2", 5, 8, 7, 6, None, 8),
    "Red Giant":    CardStats("Red Giant", 6, 7, 8, 5, None, 8),
    "Catoblepas":   CardStats("Catoblepas", 1, 9, 6, 7, None, 8),
    "Ultima Weapon":CardStats("Ultima Weapon", 7, 8, 7, 6, None, 8),
    "Chubby Chocobo":CardStats("Chubby Chocobo", 4, 9, 4, 8, None, 9),
    "Angelo":       CardStats("Angelo", 9, 3, 6, 7, None, 9),
    "Gilgamesh":    CardStats("Gilgamesh", 3, 9, 6, 7, None, 9),
    "MiniMog":      CardStats("MiniMog", 9, 2, 3, 8, None, 9),
    "Chicobo":      CardStats("Chicobo", 9, 4, 4, 8, None, 9),
    "Quezacotl":    CardStats("Quezacotl", 2, 4, 9, 9, Element.THUNDER, 9),
    "Shiva":        CardStats("Shiva", 6, 9, 7, 6, Element.ICE, 9),
    "Ifrit":        CardStats("Ifrit", 9, 8, 6, 5, Element.FIRE, 9),
    "Siren":        CardStats("Siren", 8, 9, 6, 6, None, 9),
    "Sacred":       CardStats("Sacred", 5, 9, 1, 9, Element.EARTH, 9),
    "Minotaur":     CardStats("Minotaur", 9, 7, 5, 9, Element.EARTH, 9),
    "Carbuncle":    CardStats("Carbuncle", 8, 4, 4, 9, None, 9),
    "Diablos":      CardStats("Diablos", 5, 3, 9, 9, None, 9),
    "Leviathan":    CardStats("Leviathan", 7, 7, 9, 6, Element.WATER, 9),
    "Odin":         CardStats("Odin", 8, 5, 9, 7, None, 9),
    "Pandemona":    CardStats("Pandemona", 9, 7, 6, 7, Element.WIND, 9),
    "Cerberus":     CardStats("Cerberus", 7, 6, 9, 8, None, 9),
    "Alexander":    CardStats("Alexander", 9, 6, 8, 7, Element.HOLY, 9),
    "Phoenix":      CardStats("Phoenix", 7, 9, 8, 7, Element.FIRE, 9),
    "Bahamut":      CardStats("Bahamut", 9, 8, 8, 7, None, 9),
    "Doomtrain":    CardStats("Doomtrain", 3, 9, 8, 9, Element.POISON, 9),
    "Eden":         CardStats("Eden", 9, 8, 8, 8, None, 9),
    "Ward":         CardStats("Ward", 8, 9, 7, 6, None, 9),
    "Kiros":        CardStats("Kiros", 6, 9, 7, 7, None, 9),
    "Laguna":       CardStats("Laguna", 7, 9, 8, 5, None, 9),
    "Selphie":      CardStats("Selphie", 9, 4, 9, 6, None, 9),
    "Quistis":      CardStats("Quistis", 9, 2, 4, 9, None, 9),
    "Irvine":       CardStats("Irvine", 2, 9, 9, 4, None, 9),
    "Zell":         CardStats("Zell", 8, 6, 5, 9, None, 9),
    "Rinoa":        CardStats("Rinoa", 4, 9, 9, 4, None, 9),
    "Edea":         CardStats("Edea", 9, 8, 6, 7, None, 9),
    "Seifer":       CardStats("Seifer", 6, 9, 9, 5, None, 9),
    "Squall":       CardStats("Squall", 9, 7, 9, 6, None, 9),
}