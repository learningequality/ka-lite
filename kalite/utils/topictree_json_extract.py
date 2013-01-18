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
	po.metadata = {
	    'Project-Id-Version': '1.0',
	    'Report-Msgid-Bugs-To': 'you@example.com',
	    'POT-Creation-Date': '2007-10-18 14:00+0100',
	    'PO-Revision-Date': '2007-10-18 14:00+0100',
	    'Last-Translator': 'you <you@example.com>',
	    'Language-Team': 'English <yourteam@example.com>',
	    'MIME-Version': '1.0',
	    'Content-Type': 'text/plain; charset=utf-8',
	    'Content-Transfer-Encoding': '8bit',
	}

	# Append titles & descriptions 
	for node in nodes:
		for key in ["title", "description"]:
			if not node.get(key) or node.get("kind") == "Separator":
				continue
			entry = polib.POEntry(
			    msgid= node.get(key),
			    msgstr='',
			    msgctxt="%s %s" %(node["kind"], key)
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
	mathnode = rootnode.get("children")[0]
	arithmetic_prealgebra_node = mathnode.get("children")[0]
	node_info(rootnode, for_bill)
	node_info(mathnode, for_bill)
	node_info(arithmetic_prealgebra_node, for_bill)
	for i in range(0, 4):
		for_bill += recurse_json(arithmetic_prealgebra_node.get("children")[i])

	generate_po(for_bill, 'decimals.po')


def sitewide_po():
	translatable_json = recurse_json(rootnode)
	generate_po(translatable_json, 'topics.po')


decimals_for_bill()
sitewide_po()





