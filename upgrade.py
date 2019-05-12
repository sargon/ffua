#!/usr/bin/env python3

import logging

import click
from ffua.graph import spantree, addVirtualNode
from ffua.hopglass import getDataFromHopGlass
from ffua.mechanism import mechanismFactory, mechansim_dict
from ffua.htaccess import generateHtAccessRulesForBranch
from ffua.config import Config
from ffua.upgrade import UpgradeModel

@click.command()
@click.option("--debug/--no-debug",default=False,help="Debugging output")
@click.option('--config', '-c', 'config_file', type=click.File(mode='r'), prompt=True)
@click.argument('mechanism', default="outerToInnerUpgrade",type=click.Choice(mechansim_dict.keys()))
def cli(debug, config_file,mechanism):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = Config()
    config.load(config_file)
    hopglass = config.hopglass
    startnode = config.startnodes

    graph = getDataFromHopGlass(hopglass)
    if config.has_virtal_rootnode():
        # Construct virtual node and add a link to all startnodes.
        startnode = addVirtualNode(graph,startnode)
    else:
        startnode = graph.getGraphIdentFromIdent(startnode[0])
    tree = spantree(graph, startnode)

    mechanism = mechanismFactory(mechanism,config)
    upgrade = UpgradeModel(graph,tree,mechanism)
    for branch, generator in upgrade(config):
        generateHtAccessRulesForBranch(branch, generator, config)


if __name__ == "__main__":
    cli(obj={})
