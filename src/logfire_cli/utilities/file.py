from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import BaseModel


def load_dict_from_yaml(path: Path) -> dict[str, Any]:
    """Load a dictionary from a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        The loaded dictionary.
    """
    with path.open() as f:
        loaded: Any = yaml.safe_load(f)  # pyright: ignore[reportAny]

    if not isinstance(loaded, dict):
        msg = 'Invalid YAML file: expected a dictionary'
        raise TypeError(msg)

    if not all(isinstance(key, str) for key in loaded):  # pyright: ignore[reportUnknownVariableType]
        msg = 'Invalid YAML file: expected all keys to be strings'
        raise TypeError(msg)

    return cast('dict[str, Any]', loaded)


def load_model_from_yaml[T: BaseModel](path: Path, model: type[T]) -> T:
    """Load a model from a YAML file.

    Args:
        path: Path to the YAML file.
        model: Model to load.

    Returns:
        The loaded model.

    Raises:
        TypeError: If the YAML is not a dictionary.
        ValueError: If the YAML is not a valid model.
    """
    loaded = load_dict_from_yaml(path)
    return model.model_validate(loaded)

def dump_model_to_yaml(model: BaseModel) -> str:
    """Dump a model to a YAML file.

    Args:
        model: Model to dump.
        path: Path to the YAML file.
    """
    return yaml.dump(model.model_dump(mode='json', by_alias=True, exclude_none=True), default_flow_style=False, sort_keys=False, allow_unicode=True)

def dump_model_to_yaml_file(model: BaseModel, path: Path) -> None:
    """Dump a model to a YAML file.

    Args:
        model: Model to dump.
        path: Path to the YAML file.
    """
    with path.open('w') as f:
        _ = f.write(dump_model_to_yaml(model=model))