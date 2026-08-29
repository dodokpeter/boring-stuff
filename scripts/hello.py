#! python3
from core.configuration.user_conf import create_config_path, load_config, save_config


def main():
    print('--- 🛠️ BoringStuff Initializer ---')

    name = input('What is your name? ')
    surname = input('What is your surname? ')
    age = input('What is your age? ')

    config = load_config(None)
    config.setdefault('me', {})
    config['me']['name'] = name
    config['me']['surname'] = surname
    try:
        config['me']['age'] = int(age)
    except ValueError:
        config['me']['age'] = age  # Keep as string if not a number

    save_config(None, config)

    print(f'\n✅ Success! Nice to meet you, {name}.')
    print(f'Values saved to: {create_config_path(None)}')
    print(f'Next year you will be {int(age) + 1}!')


if __name__ == "__main__":
    main()
