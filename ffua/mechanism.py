import attr
from datetime import datetime, timedelta
import logging



def has_active_childs(graph,tree,fwv,node):
    """
    Check if a node has active childs in the tree.
    A child is active when it is offline or already has active firmware.
    """
    now = datetime.utcnow()
    for gchild,_ in tree.getOutEdges(node).items():
        data = graph.getNodeData(gchild)
        lastseen = data.getLastSeen()
        if data.getFirmwareVersion() in fwv:
            continue
        elif lastseen is not None:
            if now - lastseen < timedelta(minutes=30):
                return True
    return False

@attr.s
class Mechanism:
    config = attr.ib(factory=dict)

@attr.s
class OuterToInnerUpgrade(Mechanism):
    """
    Allow updates only for the leafs of the spantree of the network graph.
    Except for the situation where every child of a node is inactive.
    """
    
    def __call__(self,graph,tree,branches):

        fwv = list(map(lambda b: b.getFirmwareVersion().pop() ,branches.values()))

        for node in tree.getNodes():
            nodedata = graph.getNodeData(node)
            if nodedata is None:
                gn = graph.getNode(node)
                logging.info(f"Node { gn.ident } has no nodedata")
            try:
                if tree.getNode(node).degree() == 1:
                    yield nodedata
                elif not has_active_childs(graph, tree, fwv, node):
                    yield nodedata
            except Exception as e:
                logging.exception(e)

class MiauEnforce(Mechanism):
    """
    Enforce miau usage by allowing all nodes with distance less 
    equal to min_distance the update and every node already 
    running the right version.
    """

    def __init__(self,config):
        if not 'min_distance' in config:
            config['min_distance'] = 1
        if 'virtual_rootnode' in config:
            if config['virtual_rootnode']:
                config['min_distance'] += 1
        super().__init__(config)

    def __call__(self,graph,tree,branches):

        targetversions = list(map(lambda b: b.getFirmwareVersion().pop() ,branches.values()))
        targetbranches = branches.keys()

        for node in tree.getNodes():
            distance = tree.getNodeData(node)
            nodedata = graph.getNodeData(node)
            try:
                if distance <= self.config['min_distance']:
                    yield nodedata
                elif distance > self.config['min_distance']:
                    version = nodedata.getFirmwareVersion()
                    if version in targetversions:
                        yield nodedata
                        continue
                    branch = nodedata.getBranch()
                    if branch not in targetbranches:
                        yield nodedata
            except Exception as e:
                logging.exception(e)

mechansim_dict = {
        'outerToInnerUpgrade': OuterToInnerUpgrade,
        'miauEnforce': MiauEnforce
        }

def mechanismFactory(name,config):
    if name in mechansim_dict:
        config = config.get_mechansim(name)
        return mechansim_dict[name](config)
    else:
        raise Exeption(f"Unknown mechansim { name }")
