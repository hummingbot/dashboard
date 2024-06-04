import random


def generate_random_name(existing_names_list):
    # Convert the list to a set for efficient lookup
    existing_names = set(existing_names_list)

    money_related = ["Dollar", "Coin", "Credit", "Wealth", "Fortune", "Cash", "Gold", "Profit", "Rich", "Value"]
    trading_related = ["Market", "Trade", "Exchange", "Broker", "Stock", "Bond", "Option", "Margin", "Future", "Index"]
    algorithm_related = ["Algo", "Bot", "Code", "Script", "Logic", "Matrix", "Compute", "Sequence", "Data", "Binary"]
    science_related = ["Quantum", "Neuron", "Atom", "Fusion", "Gravity", "Particle", "Genome", "Spectrum", "Theory",
                       "Experiment"]
    space_related = ["Galaxy", "Nebula", "Star", "Planet", "Orbit", "Cosmos", "Asteroid", "Comet", "Blackhole",
                     "Eclipse"]
    bird_related = ["Falcon", "Eagle", "Hawk", "Sparrow", "Robin", "Swallow", "Owl", "Raven", "Dove", "Phoenix"]

    categories = [money_related, trading_related, algorithm_related, science_related, space_related, bird_related]

    while True:
        # Select two different categories
        first_category = random.choice(categories)
        second_category = random.choice([category for category in categories if category != first_category])

        # Select one word from each category
        first_word = random.choice(first_category)
        second_word = random.choice(second_category)

        name = f"{first_word}-{second_word}"

        if name not in existing_names:
            existing_names.add(name)
            existing_names_list.append(name)  # Update the list to keep track of used names
            return name