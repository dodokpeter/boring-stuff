from pathlib import Path

import yaml

from core.console.inputs import ask_string_value

DEFAULT_CONFIG_NAME = "BoringStuff.yml"


class MissingConfigError(Exception):
    """Raised by load_config_value when a required value couldn't be
    obtained - no terminal was attached to prompt for it, or the user
    cancelled the prompt."""


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


def load_config_value(config_name, message, default, *config_keys, validate=None):
    """Look up a (possibly nested) config value by a path of keys - e.g.
    `load_config_value(None, "Wallpaper directory", None, "wallpaper", "directory")`
    for `config['wallpaper']['directory']`. If missing, prompts for it
    (`default=None` makes it required - see ask_string_value) and persists
    it back into the config so it's only asked once.

    `validate`, if given, is called with the typed answer; it should raise
    ValueError (whose message is shown) to reject the answer and re-prompt.

    Raises MissingConfigError if the value couldn't be obtained - no
    terminal attached (EOFError) or the prompt was cancelled
    (KeyboardInterrupt)."""
    if not config_keys:
        raise ValueError("load_config_value requires at least one config key")

    config = load_config(config_name)
    node = config
    for key in config_keys[:-1]:
        node = node.setdefault(key, {})
    last_key = config_keys[-1]

    value = node.get(last_key)
    if value is not None:
        return value

    while True:
        try:
            value = ask_string_value(message, default)
        except EOFError as e:
            raise MissingConfigError(f"{message} is not configured, and no terminal is attached to ask for it.") from e
        except KeyboardInterrupt as e:
            raise MissingConfigError(f"Cancelled - {message} is still not configured.") from e

        if validate is None:
            break
        try:
            validate(value)
            break
        except ValueError as e:
            print(e)

    node[last_key] = value
    save_config(config_name, config)
    return value
