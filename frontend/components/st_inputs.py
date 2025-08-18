from math import exp

from _decimal import Decimal
from hummingbot.strategy_v2.utils.distributions import Distributions


def normalize(values):
    total = sum(values)
    return [val / total for val in values]


def distribution_inputs(column, dist_type_name, levels=3, default_values=None):
    if dist_type_name == "Spread":
        dist_type = column.selectbox(
            f"Type of {dist_type_name} Distribution",
            ("Manual", "GeoCustom", "Geometric", "Fibonacci", "Logarithmic", "Arithmetic", "Linear"),
            key=f"{column}_{dist_type_name.lower()}_dist_type",
            # Set the default value
        )
    else:
        dist_type = column.selectbox(
            f"Type of {dist_type_name} Distribution",
            ("Manual", "Geometric", "Fibonacci", "Logarithmic", "Arithmetic"),
            key=f"{column}_{dist_type_name.lower()}_dist_type",
            # Set the default value
        )
    base, scaling_factor, step, ratio, manual_values = None, None, None, None, None

    if dist_type != "Manual":
        start = column.number_input(f"{dist_type_name} Start Value", value=1.0,
                                    key=f"{column}_{dist_type_name.lower()}_start")
        if dist_type == "Logarithmic":
            base = column.number_input(f"{dist_type_name} Log Base", value=exp(1),
                                       key=f"{column}_{dist_type_name.lower()}_base")
            scaling_factor = column.number_input(f"{dist_type_name} Scaling Factor", value=2.0,
                                                 key=f"{column}_{dist_type_name.lower()}_scaling")
        elif dist_type == "Arithmetic":
            step = column.number_input(f"{dist_type_name} Step", value=0.3,
                                       key=f"{column}_{dist_type_name.lower()}_step")
        elif dist_type == "Geometric":
            ratio = column.number_input(f"{dist_type_name} Ratio", value=2.0,
                                        key=f"{column}_{dist_type_name.lower()}_ratio")
        elif dist_type == "GeoCustom":
            ratio = column.number_input(f"{dist_type_name} Ratio", value=2.0,
                                        key=f"{column}_{dist_type_name.lower()}_ratio")
        elif dist_type == "Linear":
            step = column.number_input(f"{dist_type_name} End", value=1.0,
                                       key=f"{column}_{dist_type_name.lower()}_end")
    else:
        if default_values:
            manual_values = [column.number_input(f"{dist_type_name} for level {i + 1}", 
                                                 value=value * 100.0,
                                                 min_value=0.01 if dist_type_name == "Amount" else 0.0,
                                                 help="Value must be greater than 0" if dist_type_name == "Amount" else None,
                                                 key=f"{column}_{dist_type_name.lower()}_{i}") for i, value in
                             enumerate(default_values)]
        else:
            manual_values = [column.number_input(f"{dist_type_name} for level {i + 1}", 
                                                 value=i + 1.0,
                                                 min_value=0.01 if dist_type_name == "Amount" else 0.0,
                                                 help="Value must be greater than 0" if dist_type_name == "Amount" else None,
                                                 key=f"{column}_{dist_type_name.lower()}_{i}") for i, value in
                             range(levels)]
        start = None  # As start is not relevant for Manual type

    return dist_type, start, base, scaling_factor, step, ratio, manual_values


def get_distribution(dist_type, n_levels, start, base=None, scaling_factor=None, step=None, ratio=None,
                     manual_values=None):
    distribution = []
    if dist_type == "Manual":
        distribution = manual_values
    elif dist_type == "Linear":
        distribution = Distributions.linear(n_levels, start, step)
    elif dist_type == "Fibonacci":
        distribution = Distributions.fibonacci(n_levels, start)
    elif dist_type == "Logarithmic":
        distribution = Distributions.logarithmic(n_levels, base, scaling_factor, start)
    elif dist_type == "Arithmetic":
        distribution = Distributions.arithmetic(n_levels, start, step)
    elif dist_type == "Geometric":
        distribution = Distributions.geometric(n_levels, start, ratio)
    elif dist_type == "GeoCustom":
        distribution = [Decimal("0")] + Distributions.geometric(n_levels - 1, start, ratio)
    return [float(val) for val in distribution]
