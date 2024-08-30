import functools
import logging
import pathlib as plb

logger = logging.getLogger("manuel._dialects.utils")


def _path_valid(path: plb.Path) -> plb.Path:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path


def read_sql_file(path: plb.Path) -> str:
    path = plb.Path(path).resolve()
    logger.debug("Reading file: %s", path)
    with _path_valid(path).open("r") as f:
        return f.read()


def requires_extra(library_name: str, extra_name: str, extra_installed: bool):
    @functools.wraps
    def decorator(function):
        def wrapper(*args, **kwargs):
            if not extra_installed:
                raise ImportError(
                    f"{library_name} is not installed. Install Manuel with the '{extra_name}' extra using 'pip install manuel[{extra_name}]'"
                )
            return function(*args, **kwargs)

        return wrapper

    return decorator
