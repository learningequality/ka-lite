import json
import pdb
import polib

rootnode = json.loads(open("../static/data/topics.json").read())

def recurse_json(node):
	## Returns list of key value pairs for translation
	## optional param will recurse until it hits a node of that title

	# Titles list to store translatable titles 
	nodes = []

	# First check to see if inside a node with translatable elements
	if node.get("title"):
		node_info = {
		"title": node.get("title"),
		"description": node.get("description"),
		"kind": node.get("kind")
		}
		nodes.append(node_info)

	# Walk through each child, calling recurse_json 
	for child in node.get("children", []):
		nodes += recurse_json(child)
	return nodes 
 

def generate_po(nodes, filename):
	# Create po file 
	po = polib.POFile()

	# Append titles & descriptions 
	string_set = set()
	for node in nodes:
		for key in ["title", "description"]:
			value = node.get(key)
			if not value or node.get("kind") == "Separator":
				continue
			if value in string_set:
				continue
			string_set.add(value)
			entry = polib.POEntry(
			    msgid= value,
			    msgstr= "",
			    comment="%s %s" %(node["kind"], key)
			)
			po.append(entry)

	# Save()
	po.save(filename)


def node_info(node, lst):
	if node.get("title"):
		node_info = {
		"title": node.get("title"),
		"description": node.get("description"),
		"kind": node.get("kind")
		}
		lst.append(node_info)
	return lst


def decimals_for_bill():
	for_bill = []

	#top level
	node_info(rootnode, for_bill)

	#2nd level e.g. Math, Science & Econ, etc. 
	for i in range(0, 4):
		node_info(rootnode.get("children")[i], for_bill)

	#3rd level e.g. Arithmetic & Prealgebra, etc
	mathnode = rootnode.get("children")[0]
	for i in range(0, 11):
		node_info(mathnode.get("children")[i], for_bill)

	#4th Level e.g.
	arithmetic_prealgebra_node = mathnode.get("children")[0]
	for i in range(0, 10):
		node_info(arithmetic_prealgebra_node.get("children")[i], for_bill)
	
	#5th Level e.g. all children up until decimals 
	# for i in range(0, 5):
	for_bill += recurse_json(arithmetic_prealgebra_node.get("children")[0])

	generate_po(for_bill, 'demo.po')


def sitewide_po():
	translatable_json = recurse_json(rootnode)
	generate_po(translatable_json, 'topics.po')


decimals_for_bill()
# sitewide_po()





