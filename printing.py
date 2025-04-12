from enum import Enum


class Color(Enum):
	RED = 91
	GREEN = 92
	YELLOW = 93
	BLUE = 94
	PURPLE = 95
	CYAN = 96
	RESET = 0


def print_color(message: str, color: Color):
	print(f"\n\033[{color.value}m{message}\033[{Color.RESET.value}m\n")
