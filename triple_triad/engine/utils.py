import random


def random_rules():
    "Pick a random subset of rule for a torunament game"
    avaiable = ["Open", "Same", "Plus", "Random"]
    count = random.randint(0, 2)
    return set(random.sample(avaiable, count))


def reset_card_owners(*hands):
    "Reset all hands in the given list to have no owner"
    for hand in hands:
        for card in hand:
            card.owner = None
