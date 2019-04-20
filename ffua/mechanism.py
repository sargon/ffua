from datetime import datetime, timedelta
import logging

def outerToInnerUpgrade(graph,tree):
    """
    Allow updates only for the leafs of the spantree of the network graph.
    Except for the situation where every child of a node is inactive.
    """

    def has_active_childs(node):
        now = datetime.utcnow()
        for gchild,_ in tree.getOutEdges(node).items():
            lastseen = graph.getNodeData(gchild).getLastSeen()
            if lastseen is not None:
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
        except Exception as e:
            logging.exception(e)

def miauEnforce(graph,tree,targetfirmwares,min_distance=2):
    """
    Enforce miau usage by allowing all nodes with distance less 
    equal to min_distance the update and every node already 
    running the right version.
    """

    targetversions = [ v for _,v in targetfirmwares ]
    targetbranches = [ b for b,_ in targetfirmwares ]

    for node in tree.getNodes():
        distance = tree.getNodeData(node)
        nodedata = graph.getNodeData(node)
        try:
            if distance <= min_distance:
                yield nodedata
            elif distance > min_distance:
                version = nodedata.getFirmwareVersion()
                if version in targetversions:
                    yield nodedata
                    continue
                branch = nodedata.getBranch()
                if branch not in targetbranches:
                    yield nodedata
        except Exception as e:
            logging.exception(e)

