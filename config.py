import re
from ConfigParser import ConfigParser

from core import Size, Gravity, WindowManager


# Predefined sizes that can be used in config files
SIZES = {'FULL': '1.0',
         'HALF': '0.5',
         'THIRD': '1.0/3',
         'QUARTER': '0.25'}

# Predefined gravities, that can be used in config files
GRAVITIES = {'TOP_LEFT': Gravity(0, 0),
             'TOP': Gravity(0.5, 0),
             'TOP_RIGHT': Gravity(1, 0),
             'LEFT': Gravity(0, 0.5),
             'MIDDLE': Gravity(0.5, 0.5),
             'RIGHT': Gravity(1, 0.5),
             'BOTTOM_LEFT': Gravity(0, 1),
             'BOTTOM': Gravity(0.5, 1),
             'BOTTOM_RIGHT': Gravity(1, 1)}

# Pattern matching simple calculations with floating numbers
PATTERN = re.compile('^[ 0-9\.\+-/\*]+$')

CONFIG = ConfigParser()

def parse_size(widths, heights):
    """Parse widths and heights strings and return Size object.

    It can be float number (value will be evaluatedi, so 1.0/2 is valid) 
    or predefined value in SIZES.

    """
    for old, new in SIZES.items():
        widths = widths.replace(old, new)
        heights = heights.replace(old, new)
    width = [eval(width) for width in widths.split(', ')
                         if PATTERN.match(width)]
    height = [eval(height) for height in heights.split(', ')
                           if PATTERN.match(height)]
    return Size(width, height)


def parse_gravity(gravity):
    """Parse gravity string and return Gravity object.

    It can be one of predefined GRAVITIES, or x and y values (floating
    numbers or those described in SIZES).

    """
    if gravity in GRAVITIES:
        return GRAVITIES[gravity]
    for old, new in SIZES.items():
        gravity = gravity.replace(old, new)
    x, y = [eval(xy) for xy in gravity.split(', ')
                     if PATTERN.match(xy)]
    return Gravity(x, y)


def load(filename):

    """Load configuration file"""

    CONFIG.read(filename) #TODO: various places?

    keys = {}
    mappings = {}

    for key, value in CONFIG.items('KEYS'):
        keys[key] = value

    CONFIG.remove_section('KEYS')

    for section in CONFIG.sections():
        data = {}
        for key, value in CONFIG.items(section):
            data[key] = value

        #TODO: globals()? maybe GRAVITIES dict?
        direction = parse_gravity(data['direction'])
        position  = parse_gravity(data['position'])
        if 'gravity' in data:
            gravity = parse_gravity(data['gravity'])
        else:
            gravity = position

        sizes = parse_size(data['widths'], data['heights'])

        mask_key = keys[section]

        mask_code = WindowManager.keycode(keys['put'], mask_key)
        mappings[mask_code] = ['put', position]
        mask_code = WindowManager.keycode(keys['grid_width'], mask_key)
        mappings[mask_code] = ['grid', position, gravity, sizes, 'width']
        mask_code = WindowManager.keycode(keys['grid_height'], mask_key)
        mappings[mask_code] = ['grid', position, gravity, sizes, 'height']

        mask_code = WindowManager.keycode(keys['hover'], mask_key)
        mappings[mask_code] = ['hover', direction]
        mask_code = WindowManager.keycode(keys['expand'], mask_key)
        mappings[mask_code] = ['expand', direction]
        mask_code = WindowManager.keycode(keys['shrink'], mask_key)
        mappings[mask_code] = ['shrink', direction]

    mask_code = WindowManager.keycode(keys['exit'])
    mappings[mask_code] = ['exit']

    mask_code = WindowManager.keycode(keys['info'])
    mappings[mask_code] = ['test']

    mask_code = WindowManager.keycode(keys['reload'])
    mappings[mask_code] = ['reload']

    return mappings

