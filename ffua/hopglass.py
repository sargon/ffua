import requests
from ffua.graph import Graph
from ffua.node import NodeMetaData

def getDataFromHopGlass(url):
    graphurl = url + "/graph.json"
    nodesurl = url + "/nodes.json"
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
                graph.setNodeData(cnt,NodeMetaData(node_id,nodemap[node_id]))
                graph.setNodeIdent(cnt,node_id)
            else:
                node_id = node['id'].replace(':','')
                graph.setNodeIdent(cnt,node_id)
            cnt = cnt + 1
        for link in jgraph['batadv']['links']:
            graph.addEdge(link['source'],link['target'],link['tq'])

    return graph
