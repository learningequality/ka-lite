import os

from fle_utils.importing import import_all_from

import_all_from(os.path.dirname(__file__), locals(), globals())