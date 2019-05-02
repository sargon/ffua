#!/usr/bin/env python3

import logging
import sys

import click
from ffua.graph import spantree, addVirtualNode, getSubtreeNodes, getTreeSubtrees, clone_graph
from ffua.hopglass import getDataFromHopGlass
from ffua.mechanism import outerToInnerUpgrade, miauEnforce
from ffua.htaccess import generateHtAccessRulesForBranches, generateHtAccessRulesForBranch
from ffua.config import Config

@click.group()
@click.option("--debug/--no-debug",default=False,help="Debugging output")
@click.option('--config', '-c', 'config_file', type=click.File(mode='r'), prompt=True)
@click.pass_context
def cli(ctx, debug, config_file):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = Config()
    config.load(config_file)
    hopglass = config.hopglass
    startnode = config.startnodes

    graph = getDataFromHopGlass(hopglass)
    if len(startnode) > 1:
        # Construct virtual node and add a link to all startnodes.
        startnode = addVirtualNode(graph,startnode)
        ctx.obj['virtual_rootnode'] = True
    else:
        startnode = graph.getGraphIdentFromIdent(startnode[0])
        ctx.obj['virtual_rootnode'] = False
    tree = spantree(graph, startnode)
    ctx.obj['config'] = config
    ctx.obj['graph'] = graph
    ctx.obj['tree'] = tree
    ctx.obj['rootnode'] = startnode

@cli.command(name="miauEnforce")
@click.option("--min-distance", "-d", type=click.INT, default=2)
@click.pass_context
def miau(ctx, min_distance):
    firmware = [ (name,mfst.getFirmwareVersion().pop()) for name,mfst in ctx.obj['config'].branches.items()]
    graph = ctx.obj['graph']
    tree = ctx.obj['tree']
    if ctx.obj['virtual_rootnode']:
        min_distance += 1
    generator = miauEnforce(graph, tree, firmware, min_distance)
    generateHtAccessRulesForBranches(generator, ctx.obj['config'])

@cli.command(name="outerToInnerUpgrade")
@click.pass_context
def otiu(ctx):
    graph = ctx.obj['graph']
    config = ctx.obj['config']
    
    subtrees = list(getTreeSubtrees(graph,ctx.obj['tree'],ctx.obj['rootnode']))
    for branch in config.branches:
        tree = clone_graph(ctx.obj['tree'])
        num_compatible = 0
        for st in subtrees:
            for stn in getSubtreeNodes(tree,st):
                data = graph.getNodeData(stn)
                if data.getBranch() in config.incompatible[branch]:
                    for stn in getSubtreeNodes(tree,st):
                        std = graph.getNodeData(stn)
                        tree.removeNode(stn)
                    break
        logging.debug(f"Branch: { branch } ; Nodes in Tree: { tree.numNodes() }")
        generator = outerToInnerUpgrade(graph, tree,ctx.obj['config'].branches)
        generateHtAccessRulesForBranch(branch,generator, ctx.obj['config'])

if __name__ == "__main__":
    cli(obj={})
