"""poetry run python -m scripts.exchanges"""

from iso10383 import MIC


def print_fields(obj, indent=2):
    for k in vars(obj):
        v = getattr(obj, k)
        # If the value is a MICEntry, recursively print its fields
        if hasattr(v, "__class__") and v.__class__.__name__ == "MICEntry":
            print(f"{' ' * indent}{k} (MICEntry):")
            print_fields(v, indent + 2)
        else:
            print(f"{' ' * indent}{k}: {v}")


for exchange in MIC:
    print("Exchange:")
    print_fields(exchange.value, indent=2)
    print()
