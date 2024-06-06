import random


def generate_random_name(existing_names_list):
    # Convert the list to a set for efficient lookup
    existing_names = set(existing_names_list)

    money_related = ["dollar", "coin", "credit", "wealth", "fortune", "cash", "gold", "profit", "rich", "value"]
    trading_related = ["market", "trade", "exchange", "broker", "stock", "bond", "option", "margin", "future", "index"]
    algorithm_related = ["algo", "bot", "code", "script", "logic", "matrix", "compute", "sequence", "data", "binary"]
    science_related = ["quantum", "neuron", "atom", "fusion", "gravity", "particle", "genome", "spectrum", "theory",
                       "experiment"]
    space_related = ["galaxy", "nebula", "star", "planet", "orbit", "cosmos", "asteroid", "comet", "blackhole",
                     "eclipse"]
    bird_related = ["falcon", "eagle", "hawk", "sparrow", "robin", "swallow", "owl", "raven", "dove", "phoenix"]

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
