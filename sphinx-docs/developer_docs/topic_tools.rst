topic_tools app
===============

The purpose of this document is to track the development of the topic_tools app.

The Topic Tree
--------------

The topic tree is a hierarchical representation of real data (exercises, and videos).
Leaf nodes of the tree are real learning resources, such as videos and exercises.
Non-leaf nodes are topics, which describe a progressively higher-level grouping of the topic data.

Each node in the topic tree comes with lots of metadata, including:
* title
* description
* id (unique identifier; now equivalent to slug below)
* slug (for computing a URL)
* path (which is equivalent to a URL)
* kind (Topic, Exercise, Video)
and more.

The attributes available will vary depending on the kind of the node.

A topic tree node also has an associated channel. Nodes with different channels should be disjoint, in the graph-theoretical sense.
That is, all the children of a node, all the ancestors of a node, and all the children of all the ancestors of a node should all have the same channel.

API
---

API description goes here.