import yaml
import os

from core.console.inputs import ask_string_value

HOME_DIRECTORY = os.environ['HOME']
CONFIG_DIRECTORY = os.sep + '.boring-stuff'
HOME_CONFIG_DIRECTORY = HOME_DIRECTORY + CONFIG_DIRECTORY + os.sep


def create_config_path(config_name):
    if config_name is None:
        return HOME_CONFIG_DIRECTORY + 'BoringStuff.yml'
    else:
        config = HOME_CONFIG_DIRECTORY + config_name
        if not os.path.isfile(config):
            f = open(config, "w")
            f.write("# This is config file: " + config_name)
            f.write("\n")
            f.write("app: boring-stuff")
            f.close()
        return config


# return type is dictionary f.e.: prime_service['rest']['url']
def load_config(config_name):
    config = create_config_path(config_name)
    with open(config, 'r') as yaml_file:
        return yaml.safe_load(yaml_file)


def save_config(config_name, obj):
    config = create_config_path(config_name)
    with open(config, 'w') as yaml_file:
        return yaml.dump(obj, yaml_file)


def load_config_value(config_name, message, default,  config_key1):
    config = load_config(config_name)
    value = config.get(config_key1, None)
    if value is None:
        value = ask_string_value(message, default)
        # save this value
        config[config_key1] = value
        save_config(config_name, config)
        return value
