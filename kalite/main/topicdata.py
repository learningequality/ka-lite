import json
import os

import settings
from shared import topic_tools


TOPICS          = topic_tools.get_topic_tree()
NODE_CACHE      = topic_tools.get_node_cache()
ID2SLUG_MAP     = topic_tools.get_id2slug_map()
