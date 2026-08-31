#! python3
from core.configuration.user_conf import create_config_path, load_config, save_config
from core.stats import record_usage


def main():
    record_usage("hello")
    print("--- BoringStuff Initializer ---")

    name = input("What is your name? ")
    surname = input("What is your surname? ")
    age = input("What is your age? ")

    config = load_config(None)
    config.setdefault("me", {})
    config["me"]["name"] = name
    config["me"]["surname"] = surname
    age_number = None
    try:
        age_number = int(age)
        config["me"]["age"] = age_number
    except ValueError:
        config["me"]["age"] = age  # Keep as string if not a number

    save_config(None, config)

    print(f"\nSuccess! Nice to meet you, {name}.")
    print(f"Values saved to: {create_config_path(None)}")
    if age_number is not None:
        print(f"Next year you will be {age_number + 1}!")


if __name__ == "__main__":
    main()
