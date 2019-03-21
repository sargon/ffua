import attr

@attr.s
class Graph:
    """ 
    Simple directed graph.
    """

    @attr.s
    class GraphNode:
        arrows_out = attr.ib(factory=dict)
        arrows_in = attr.ib(factory=dict)
        ident = attr.ib(default=None)
        data = attr.ib(default=None)

        def degree(self):
            return len(self.arrows_in) + len(self.arrows_out)
    
    nodes = attr.ib(factory=dict)
    identmap = attr.ib(factory=dict)

    def addEdge(self,n1,n2,w):
        self.getNode(n1).arrows_out[n2] = w
        self.getNode(n2).arrows_in[n1] = w

    def getOutEdges(self,node):
        try:
            return self.getNode(node).arrows_out
        except:
            return None

    def getNode(self,node):
        if node not in self.nodes:
            self.nodes[node] = self.GraphNode()
        return self.nodes[node]

    def getNodes(self):
        return self.nodes.keys()
    
    def setNodeData(self,node,data):
        self.getNode(node).data = data 

    def setNodeIdent(self,node,ident):
        self.getNode(node).ident = ident
        self.identmap[ident] = node

    def getNodeData(self,node):
        return self.getNode(node).data

    def getNodeDataByIdent(self,ident):
        return self.getNode(self.getGraphIdentFromIdent(ident)).data

    def getGraphIdentFromIdent(self,ident):
        try:
            return self.identmap[ident]
        except:
            raise Exception(f"No graph ident for { ident }")

    def hasNode(self,n):
        return n in self.nodes

    def numNodes(self):
        return len(self.nodes)


def spantree(graph,start):
    tree = Graph()
    if not graph.hasNode(start):
       raise Exception(f"Node {start} not in graph")
    tree.getNode(start)
    maxweight = 0
    tree.setNodeData(start,0)
    nextnodes = [(start,0)]
    for node,weight in nextnodes:
        for target,_ in graph.getOutEdges(node).items():
            if not tree.hasNode(target):
                tree.addEdge(node,target,weight + 1)
                tree.setNodeData(target,weight + 1)
                maxweight = max(maxweight,weight + 1)
                nextnodes.append((target,weight+1))
    return tree

def getLeafs(tree):
    """
    Search for leafs in a graph, by the degree of nodes.
    By definition leafs have a degree equal to one. 
    """
    leafs = list()
    for node in tree.getNodes():
        # Leafs have no outgoing edges in our data model
        if tree.getNode(node).degree() == 1:
            leafs.append(node)
    return leafs
