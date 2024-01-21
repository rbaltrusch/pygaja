# -*- coding: utf-8 -*-
"""Utilities for error handling"""

import logging
from typing import Callable, TypeVar


def log_exception(message: str, exception: Exception) -> None:
    logging.exception("Message: %s. Exception: %s", message, str(exception))

AnyFunction = TypeVar("AnyFunction", bound=Callable[..., None])
def no_error(function: AnyFunction) -> AnyFunction:
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception(f"Function {function.__name__} errored due to exception %s", str(exc))
    return wrapper # type: ignore
