import yaml
import json

def load_yaml_config(config_path: str) -> dict:
    """Loads a YAML configuration file."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: YAML configuration file {config_path} not found.")
        raise
    except yaml.YAMLError as e:
        print(f"Error reading YAML configuration from {config_path}: {e}")
        raise

def load_json_config(config_path: str) -> dict:
    """Loads a JSON configuration file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON configuration file {config_path} not found.")
        raise
    except json.JSONDecodeError as e:
        print(f"Error reading JSON configuration from {config_path}: {e}")
        raise 