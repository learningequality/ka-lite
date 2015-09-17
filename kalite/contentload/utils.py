def group_by_slug(count_dict, item):
    # Build a dictionary, keyed by slug, of items that share that slug
    if item.get("slug") in count_dict:
        count_dict[item.get("slug")].append(item)
    else:
        count_dict[item.get("slug")] = [item]
    return count_dict


def dedupe_paths(topic_tree):

    def recurse_nodes(node, parent_path=""):

        children = node.get("children", [])

        if children:
            counts = reduce(group_by_slug, children, {})
            for items in counts.values():
                # Slug has more than one item!
                if len(items) > 1:
                    i = 1
                    # Rename the items
                    for item in items:
                        if item.get("kind") != "Video":
                            # Don't change video slugs, as that will break internal links from KA.
                            item["slug"] = item["slug"] + "_{i}".format(i=i)
                            item["path"] = parent_path + item["slug"] + "/"
                            i += 1
        for child in children:
            recurse_nodes(child, node.get("path"))

    recurse_nodes(topic_tree)
