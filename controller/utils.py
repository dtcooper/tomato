import board
import os


def config_bool(name: str, default: bool = False) -> bool:
    return bool(os.getenv(name.upper(), default))


def config_gpio_pin(name):
    number = os.getenv(f"{name.upper()}_PIN")
    return getattr(board, f"GP{number}")
