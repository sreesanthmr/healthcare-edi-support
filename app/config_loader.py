import json
from pathlib import Path


def load_json_config(config_path: str) -> dict:
    """
    Load a JSON configuration file.
    """

    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def load_carrier_config(config_path: str) -> dict:
    """
    Load an individual carrier EDI configuration.
    """

    return load_json_config(config_path)


def load_carriers_config(config_path: str = "config/carriers.json") -> dict:
    """
    Load the carrier registry.
    """

    return load_json_config(config_path)