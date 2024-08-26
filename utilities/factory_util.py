
import json
import random
import factory
import factory
import random


def optional_sub_factory(sub_factory, lazy=False):
    optional = random.choice([True, False, False])
    if not optional:
        return None
    return factory.SubFactory(sub_factory) if not lazy else sub_factory()


def generate_random_dict():
    random_dict = {
        "key1": random.randint(1, 10),
        "key2": random.choice(["value1", "value2", "value3"]),
        "key3": random.random(),
    }
    return random_dict


def safe_pydict():
    pydict = generate_random_dict()

    for key, value in pydict.items():
        try:
            json.dumps(value)
        except TypeError:
            pydict[key] = None

    return pydict
