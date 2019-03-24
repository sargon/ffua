#!/usr/bin/env python3

import click
import logging
import requests
import sys
import json

from ffua.graph import Graph,spantree,getLeafs
from ffua.hopglass import getDataFromHopGlass
from ffua.manifest import parse_manifest
from ffua.mechanism import outerToInnerUpgrade, miauEnforce
from ffua.htaccess import generateHtAccessRules

@click.group()
@click.option('--output','-o',type=click.File(mode='w'),default=sys.stdout)
@click.option('--config','-c',type=click.File(mode='r'),prompt=True)
@click.pass_context
def cli(ctx,output,config):
    config_map = json.load(config)
    if "hopglass" in config_map:
        hopglass = config_map['hopglass']
    else:
        logging.error("No hopglass uri defined")
        raise click.Abort()
    if "startnodes" in config_map:
        startnode = config_map['startnodes']
    else:
        logging.error("No startnodes definied")
        raise click.Abort()
    graph = getDataFromHopGlass(hopglass)
    if len(startnode) > 1:
        """
        Construct virtual node and add a link to all startnodes.
        """
        startident = graph.numNodes()
        graph.setNodeIdent(startident,"_VIRTUAL")
        num = 0
        for sn in startnode:
            try:
                nodeid = graph.getGraphIdentFromIdent(sn)
                graph.addEdge(startident,nodeid,[])
                num += 1
            except:
                logging.warning(f"Node { sn } node found in network graph")
        if num == 0:
            raise Exception("No available startnode given")
        ctx.obj['virtual_rootnode'] = True
    else:
        startident = graph.getGraphIdentFromIdent(startnode[0])
        ctx.obj['virtual_rootnode'] = False
    tree = spantree(graph,startident)
    ctx.obj['graph'] = graph
    ctx.obj['tree'] = tree
    ctx.obj['output'] = output

@cli.command(name="miauEnforce")
@click.option("--min-distance","-d",type=click.INT,default=2)
@click.argument("manifest_path",type=click.Path(exists=True,dir_okay=False))
@click.pass_context
def miau(ctx,min_distance,manifest_path):
    manifest = parse_manifest(manifest_path)
    firmware_version = manifest.getFirmwareVersion().pop()
    firmware_branch = manifest.branch
    print(f"#Tracking firmware version: { firmware_version }",file=ctx.obj['output'])
    graph = ctx.obj['graph']
    tree = ctx.obj['tree']
    if ctx.obj['virtual_rootnode']:
        min_distance += 1
    generator = miauEnforce(graph,tree,firmware_branch,firmware_version,min_distance)
    generateHtAccessRules(generator,ctx.obj['output'])
    

@cli.command(name="outerToInnerUpgrade")
@click.pass_context
def otiu(ctx):
    graph = ctx.obj['graph']
    tree = ctx.obj['tree']
    generator = outerToInnerUpgrade(graph,tree)
    generateHtAccessRules(generator,ctx.obj['output'])

if __name__ == "__main__":
    cli(obj={})
