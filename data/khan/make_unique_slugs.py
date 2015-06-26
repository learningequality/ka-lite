"""
A quick utility to fixup topics.json. We wish to ensure the constraint that sibling nodes have unique slugs.
Executing this utility with "python make_unique_slugs.py" will search the topic tree and rename slugs as needed.
The result will be in "updated_topics.json", so that you can inspect the difference before overwriting.

TODO: Fixup the contentload module to ensure this constraint is met.
"""

import json
import re

TOPICS_FILE = "topics.json"

def recurse_nodes(node):
    children = node.get("children", None)
    if children:
        for c in children:
            recurse_nodes(c)
    make_unique_child_slugs(node)

def make_unique_child_slugs(node):
    children = node.get("children", None)
    if children:
        new_children = []
        for c in children:
            base_slug = c["slug"]
            i = 2
            while c["slug"] in [x["slug"] for x in new_children]:
                c["slug"] = base_slug + "-{0}".format(i)
                i += 1
                print("{0} is a duplicate, trying {1}".format(base_slug, c["slug"]))
            if c["slug"] != base_slug:  # Update the path as well
                    c["path"] = re.sub(base_slug, c["slug"], c["path"])
            new_children.append(c)
        node["children"] = new_children

if __name__ == "__main__":
    with open(TOPICS_FILE, "r") as f:
        topics = json.load(f)
    recurse_nodes(topics)
    with open("updated_topics.json", "w") as f:
        json.dump(topics, f)
