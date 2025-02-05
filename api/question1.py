import random


def pair_gift_givers(players):
    if len(players) < 2:
        raise ValueError("At least two players are required.")

    # Shuffle the list of players to ensure randomness
    givers = players[:]
    receivers = players[:]
    random.shuffle(givers)
    random.shuffle(receivers)
    # Ensure no one is paired with themselves
    while any(giver == receiver for giver, receiver in zip(givers, receivers)):
        random.shuffle(receivers)

    # Create pairs
    pairs = [[giver, receiver] for giver, receiver in zip(givers, receivers)]
    return pairs

# Example usage
players = ["Alice", "Bob", "Charlie", "David", "Eve"]
pairs = pair_gift_givers(players)
print(pairs)