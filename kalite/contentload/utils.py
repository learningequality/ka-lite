def dedupe_paths(topic_tree):
    paths = []

    def recurse_nodes(node, parent_path):
        node["path"] = parent_path + node.get("slug") + "/"
        if node.get("path") in paths:
            i = 1
            while node.get("path") in paths:
                node["slug"] = node.get("slug") + "_{i}".format(i=i)
                node["path"] = parent_path + node.get("slug") + "/"
        paths.append(node.get("path"))
        for child in node.get("children", []):
            recurse_nodes(child, node.get("path"))
