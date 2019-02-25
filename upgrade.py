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
    
    nodes = attr.ib(factory=dict)
    g2n = attr.ib(factory=dict) 
    edgemap = attr.ib(factory=dict)

    def addEdge(self,s,t,w):
        self.addNode(s)
        self.addNode(t)
        self.edgemap[s][t] = w

    def getEdges(self,s):
        try:
            return self.edgemap[s]
        except:
            return None

    def getNodes(self):
        return self.edgemap.keys()
    
    def addNode(self,n):
        if n not in self.edgemap:
            self.edgemap[n] = dict()

    def setNodeData(self,gid,node_id,nodedata):
        self.nodes[node_id] = nodedata
        self.g2n[gid] = node_id

    def getNodeData(self,gid):
        return self.nodes[self.g2n[gid]]

    def getNodeDataById(self,node_id):
        return self.nodes[node_id]

    def getGraphIdFromNodeId(self,node_id):
        for gid,nid in self.g2n.items():
            if nid == node_id:
                return gid
        raise Exception(f"No graph ident for node_id { node_id }")

    def hasNode(self,n):
        return n in self.edgemap

    def numNodes(self):
        return len(self.edgemap)

    def numEdges(self):
        return sum([len(node) for node in self.edgemap.values()])


def spantree(graph,start):
    tree = Graph()
    if not graph.hasNode(start):
       raise Exception(f"Node {start} not in graph")
    tree.addNode(start)
    maxweight = 0
    tree.setNodeData(start,start,0)
    nextnodes = [(start,0)]
    for node,weight in nextnodes:
        for target,_ in graph.getEdges(node).items():
            if not tree.hasNode(target):
                tree.addEdge(node,target,weight + 1)
                tree.setNodeData(target,target,weight + 1)
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
        if len(tree.getEdges(node)) == 0:
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
                graph.setNodeData(cnt,node_id,nodemap[node_id])
            else:
                node_id = node['id'].replace(':','')
                graph.setNodeData(cnt,node_id,None)
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

def outerToInnerUpgrade():
    """
    Allow updates only for the leafs of the spantree of the network graph.
    Except for the situation where every child of a node is inactive.
    """

    graph = getData()

    startnode = "deadbecccc00"
    tree = spantree(graph,graph.getGraphIdFromNodeId(startnode))
    
    print("order allow,deny")
    for node in tree.getNodes():

        if len(tree.getEdges(node)) == 0:
            nodedata = graph.getNodeData(node)
            htAllowNode(nodedata)
        else:
            childs_active = False
            for gchild,_ in tree.getEdges(node).items():
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


def miauEnforce(targetversion):
    """
    Enforce miau usage by allowing all nodes with distance less equal to two
    the update and every node already running the right version.
    """

    graph = getData()

    startnode = "deadbecccc00"
    tree = spantree(graph,graph.getGraphIdFromNodeId(startnode))

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
    # outerToInnerUpgrade()
    miauEnforce("2018.1.4-612")
