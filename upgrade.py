#!/usr/bin/env python3

import logging
import sys

import click

from ffua.graph import spantree, addVirtualNode
from ffua.hopglass import getDataFromHopGlass
from ffua.mechanism import outerToInnerUpgrade, miauEnforce
from ffua.htaccess import generateHtAccessRulesForBranches
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
    tree = ctx.obj['tree']
    generator = outerToInnerUpgrade(graph, tree,ctx.obj['config'].branches)
    generateHtAccessRulesForBranches(generator, ctx.obj['config'])

if __name__ == "__main__":
    cli(obj={})
