import requests
import attr
from datetime import datetime, timedelta

graphurl = "https://hopglass.freifunk.in-kiel.de/graph.json"
nodesurl = "https://hopglass.freifunk.in-kiel.de/nodes.json"

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
            raise Exception(f"No graph ident for node_id { node_id }")

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
    print(f"# Depth: {maxweight}")
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


def getData():
    request = requests.get(nodesurl)

    if request.ok:
        nodes = request.json()
        nodemap = dict()
        for node in nodes['nodes']:
            node_id = node['nodeinfo']['node_id']
            if node_id in nodemap:
                if node['nodeinfo']['flags']['online']:
                  nodemap[node_id] = node
            else:
                nodemap[node_id] = node

    graph = Graph()
    request = requests.get(graphurl)
    if request.ok:
        jgraph = request.json()
        cnt = 0
        n2g = dict()
        g2n = dict()
        for node in jgraph['batadv']['nodes']:
            if "node_id" in node:
                node_id = node['node_id']
                graph.setNodeData(cnt,nodemap[node_id])
                graph.setNodeIdent(cnt,node_id)
            else:
                node_id = node['id'].replace(':','')
                graph.setNodeIdent(cnt,node_id)
            cnt = cnt + 1
        for link in jgraph['batadv']['links']:
            graph.addEdge(link['source'],link['target'],link['tq'])

    return graph

def htAllowNode(node):
    print(f"# { node['nodeinfo']['hostname'] }")
    print(f"# { node['nodeinfo']['software']['firmware']['release'] }")
    if "autoupdater" in node['nodeinfo']['software']:
        if "branch" in node['nodeinfo']['software']['autoupdater']:
            print(f"# { node['nodeinfo']['software']['autoupdater']['branch'] }")
    for address in node['nodeinfo']['network']['addresses']:
        print(f"allow from { address }")

def outerToInnerUpgrade(graph,tree):
    """
    Allow updates only for the leafs of the spantree of the network graph.
    Except for the situation where every child of a node is inactive.
    """
    
    print("order allow,deny")
    for node in tree.getNodes():

        if tree.getNode(node).degree() == 1:
            nodedata = graph.getNodeData(node)
            htAllowNode(nodedata)
        else:
            childs_active = False
            for gchild,_ in tree.getOutEdges(node).items():
                child = graph.getNodeData(gchild)
                lastseen =  datetime.strptime(child['lastseen'][0:18],"%Y-%m-%dT%H:%M:%S")
                now = datetime.utcnow()
                if now - lastseen < timedelta(minutes=30):
                    childs_active = True
            if not childs_active:
                nodedata = graph.getNodeData(node)
                htAllowNode(nodedata)

    print("deny from all")
    print(f"#Tree leafs: { len(getLeafs(tree)) }")


def miauEnforce(graph,tree,targetversion):
    """
    Enforce miau usage by allowing all nodes with distance less equal to two
    the update and every node already running the right version.
    """

    print("order allow,deny")
    num = 0
    for node in tree.getNodes():
        distance = tree.getNodeData(node)
        if distance == 2:
            nodedata = graph.getNodeData(node)
            htAllowNode(nodedata)
            num = num + 1
        elif distance > 2:
            nodedata = graph.getNodeData(node)
            try:
                version = nodedata['nodeinfo']['software']['firmware']['release']
                if version == targetversion:
                    htAllowNode(nodedata)
                    num = num + 1
            except:
                pass

    print("deny from all")
    print(f"#Allowed nodes: { num }")


if __name__ == "__main__":

    graph = getData()
    startnode = "deadbecccc00"
    tree = spantree(graph,graph.getGraphIdentFromIdent(startnode))

    outerToInnerUpgrade(graph,tree)
    miauEnforce(graph,tree,"2018.1.4-612")
