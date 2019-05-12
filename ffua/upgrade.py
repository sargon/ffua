import attr
import logging

from ffua.mechanism import Mechanism
from ffua.graph import Graph, Tree, getSubtreeNodes, getTreeSubtrees, clone_graph

@attr.s
class UpgradeModel:
    """
    The actual upgrade access control magic.
    This callable determines the branches which
    are compatible to a branch and applies the choosen
    mechanism. Generates htaccess files for each branch.
    """
    graph = attr.ib(type=Graph)
    tree = attr.ib(type=Tree)
    mechanism = attr.ib(type=Mechanism)

    def __call__(self,config):
        subtrees = list(getTreeSubtrees(self.graph,self.tree))
        for branch in config.branches:
            tree = clone_graph(self.tree)
            num_compatible = 0
            for st in subtrees:
                for stn in getSubtreeNodes(tree,st):
                    data = self.graph.getNodeData(stn)
                    if data.getBranch() in config.incompatible[branch]:
                        for stn in getSubtreeNodes(tree,st):
                            std = self.graph.getNodeData(stn)
                            self.tree.removeNode(stn)
                        break
            logging.debug(f"Branch: { branch } ; Nodes in Tree: { tree.numNodes() }")
            generator = self.mechanism(self.graph, self.tree, config.branches)
            yield (branch,generator)
