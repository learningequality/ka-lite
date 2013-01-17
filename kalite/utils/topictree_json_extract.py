import json

rootnode = json.loads(open("topictree.json").read())

def recurse_json(node):
	if node.get("title"):
		return [node.get("title")]
	titles = []
	for child in node.get("children", []):
		titles += recurse_json(child)
	return titles

recurse_json(rootnode)