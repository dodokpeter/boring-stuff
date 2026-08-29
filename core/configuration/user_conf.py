from pathlib import Path

import yaml

from core.console.inputs import ask_string_value

DEFAULT_CONFIG_NAME = "BoringStuff.yml"


def config_directory():
    return Path.home() / ".boring-stuff"


def create_config_path(config_name):
    config_name = config_name or DEFAULT_CONFIG_NAME
    directory = config_directory()
    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / config_name
    if not config_path.is_file():
        config_path.write_text(f"# This is config file: {config_name}\napp: boring-stuff\n", encoding="utf-8")
    return config_path


# return type is dictionary f.e.: prime_service['rest']['url']
def load_config(config_name):
    config_path = create_config_path(config_name)
    with open(config_path, "r", encoding="utf-8") as yaml_file:
        return yaml.safe_load(yaml_file) or {}


def save_config(config_name, obj):
    config_path = create_config_path(config_name)
    with open(config_path, "w", encoding="utf-8") as yaml_file:
        return yaml.dump(obj, yaml_file)


def load_config_value(config_name, message, default, config_key1):
    config = load_config(config_name)
    value = config.get(config_key1, None)
    if value is None:
        value = ask_string_value(message, default)
        # save this value
        config[config_key1] = value
        save_config(config_name, config)
    return value
