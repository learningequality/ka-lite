import json
import os

import settings
from utils import topic_tools


TOPICS          = topic_tools.get_topic_tree()
NODE_CACHE      = topic_tools.get_node_cache()
EXERCISE_TOPICS = topic_tools.get_exercise_topics()
ID2SLUG_MAP     = topic_tools.get_id2slug_map()
