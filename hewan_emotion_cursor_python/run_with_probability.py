import random

def run_with_probability(func, probability, *args, **kwargs):
    """
    Runs `func` with a given probability.

    :param func: Function to run
    :param probability: Probability to run the function (0.0 - 1.0)
    :param args: Positional arguments to pass to func
    :param kwargs: Keyword arguments to pass to func
    :return: The result of func if run, else None
    """
    if random.random() < probability:
        return func(*args, **kwargs)
    else:
        print("Function not executed due to probability check.")
        return None

