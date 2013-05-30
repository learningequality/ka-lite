from base import Plugin

class Graph(Plugin):
    "Make pretty graphs of your requests"
    active = False

    def __init__(self):
        super(Graph, self).__init__()
        self.request_graph = self.data['request_graph'] = {}
        import pygraphviz
        self.graph = pygraphviz.AGraph(directed=True)

    def urls_parsed(self, sender, fro, returned_urls, **kwargs):
        from_node = self.graph.add_node(str(fro), shape='tripleoctagon')
        for url in returned_urls:
            if not self.graph.has_node(str(url)):
                node = self.graph.add_node(str(url))
                self.graph.add_edge(str(fro), str(url))

    def finish_run(self, sender, **kwargs):
        print "Making graph of your URLs, this may take a while"
        self.graph.layout(prog='fdp')
        self.graph.draw('my_urls.png')

PLUGIN = Graph
