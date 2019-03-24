from datetime import datetime, timedelta

def outerToInnerUpgrade(graph,tree):
    """
    Allow updates only for the leafs of the spantree of the network graph.
    Except for the situation where every child of a node is inactive.
    """

    def has_active_childs(node):
        for gchild,_ in tree.getOutEdges(node).items():
            child = graph.getNodeData(gchild)
            lastseen =  datetime.strptime(child['lastseen'][0:18],"%Y-%m-%dT%H:%M:%S")
            now = datetime.utcnow()
            if now - lastseen < timedelta(minutes=30):
                return True
        return False
    
    for node in tree.getNodes():
        nodedata = graph.getNodeData(node)
        try:
            if tree.getNode(node).degree() == 1:
                yield nodedata
            elif not has_active_childs(node):
                yield nodedata
        except:
            pass

def miauEnforce(graph,tree,targetbranch,targetversion,min_distance=2):
    """
    Enforce miau usage by allowing all nodes with distance less 
    equal to min_distance the update and every node already 
    running the right version.
    """

    for node in tree.getNodes():
        distance = tree.getNodeData(node)
        nodedata = graph.getNodeData(node)
        try:
            if distance <= min_distance:
                yield nodedata
            elif distance > min_distance:
                version = nodedata['nodeinfo']['software']['firmware']['release']
                if version == targetversion:
                    yield nodedata
                    continue
                branch = node['nodeinfo']['software']['autoupdater']['branch']
                if branch != targetbranch:
                    yield nodedata
        except:
            pass

