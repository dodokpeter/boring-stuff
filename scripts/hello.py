#! python3
import yaml
import os
from pathlib import Path

def main():
    # 1. Define the path to your config file
    config_path = Path.home() / "boring-stuff" / "BoringStuff.yml"

    print('--- 🛠️ BoringStuff Initializer ---')

    # 2. Ask for user input
    name = input('What is your name? ')
    surname = input('What is your surname? ')
    age = input('What is your age? ')

    # 3. Load existing config or create an empty dict
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    else:
        print(f"⚠️ Config not found at {config_path}. Creating a new one.")
        config = {'me': {}, 'pinterest': {'randomBoard': ''}}

    # 4. Update the values
    if 'me' not in config:
        config['me'] = {}

    config['me']['name'] = name
    config['me']['surname'] = surname
    try:
        config['me']['age'] = int(age)
    except ValueError:
        config['me']['age'] = age # Keep as string if not a number

    # 5. Save back to the YAML file
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f'\n✅ Success! Nice to meet you, {name}.')
    print(f'Values saved to: {config_path}')
    print(f'Next year you will be {int(age) + 1}!')

if __name__ == "__main__":
    main()