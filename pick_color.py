"""
Usage: `python pick_color.py <name of color>`

Example: `python pick_color.py blue` will return all blue colors.
"""
import sys
from pygame.colordict import THECOLORS
from pprint import  pprint

color_list = [(c, v) for c, v in THECOLORS.items() if sys.argv[1] in c]
pprint(color_list)
