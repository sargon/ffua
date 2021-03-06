import attr
import logging

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

        def isNeighbor(self,node_id):
            return node_id in self.arrows_out or node_id in self.arrows_in
    
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

    def getNodeData(self,node):
        if node in self.nodes:
            return self.nodes[node].data
        else:
            raise Exception(f"No such node { node }")

    def removeNode(self,node):
        if node in self.nodes:
            gnode = self.nodes[node]
            for neighbor in gnode.arrows_out:
                del self.nodes[neighbor].arrows_in[node]
            for neighbor in gnode.arrows_in:
                del self.nodes[neighbor].arrows_out[node]
            del self.nodes[node]
        assert node not in self.nodes

    def getNodes(self):
        return self.nodes.keys()

    def getEdges(self):
        for node in self.nodes.keys():
            for neighbor in self.getNode(node).arrows_out:
                yield (node,neighbor)
    
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


@attr.s
class Tree(Graph):
    root_node = attr.ib(default=None)


def clone_graph(graph):
    """
    Clone the graph structure, nodedata is only referenced.
    Edge weights are ignored.
    """
    clone = Graph()
    for n1,n2 in graph.getEdges():
        clone.addEdge(n1,n2,None)
    for node in graph.nodes:
        clone.setNodeData(node,graph.getNodeData(node))

    return graph


def spantree(graph,start):
    tree = Tree()
    tree.root_node = start
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


def getTreeSubtrees(graph,tree):
    """
    Generates a list of childs which are connected.
    to the starting center of the network. They are
    the representatives of the subtrees.
    """
    childs = list(tree.getOutEdges(tree.root_node).keys())
    logging.debug(f"Starting childs: { childs }")
    while len(childs) > 0:
        child = childs.pop()
        child_data = graph.getNodeData(child)
        if child_data.isStartNode():
            logging.debug(f"Node { child } is a starting node")
            childs.extend(tree.getOutEdges(child).keys())
        else:
            yield child

def getSubtreeNodes(tree,child):
    """
    Starting from child walks upwards in the graph, and returns
    a stream of childs in the subtree.
    """
    childs = list(tree.getOutEdges(child).keys())
    yield child

    while len(childs) > 0:
        cld = childs.pop()
        childs.extend(tree.getOutEdges(cld).keys())
        yield cld

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

def addVirtualNode(graph,neighbors):
    virtual_id = graph.numNodes()
    graph.setNodeIdent(virtual_id, "_VIRTUAL")
    num = 0
    for neighbor in neighbors:
        try:
            nodeid = graph.getGraphIdentFromIdent(neighbor)
            data = graph.getNodeData(nodeid)
            data.startnode = True
            graph.addEdge(virtual_id, nodeid, [])
            num += 1
        except:
            logging.warning(f"Node { neighbor } node found in network graph")
    if num == 0:
        raise Exception("No available neighbors given")
    else:
        return virtual_id

def getComponents(graph):
    """
    Disassemble the graph into its connectivity components.
    """

    def findComponent(components,node):
        # Search existing components
        for component in components:
            if node in component:
                return component
        # None found return a new one
        component = set()
        component.add(node)
        components.append(component)
        return component

    def joinComponents(components, comp1, comp2):
        if comp1 is comp2:
            # Already the same component
            return
        else:
            comp1.update(comp2)
            components.remove(comp2)


    components = []
    for src,dst in graph.getEdges():
        sc = findComponent(components,src)
        dc = findComponent(components,dst)
        joinComponents(components,sc,dc)

    return components

def isConnectedTo(graph,node_id):
    """
    Checks if all nodes in the graph are connected to given node.
    """
    len(getComponents(graph)) == 1

