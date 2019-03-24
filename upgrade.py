#!/usr/bin/env python3

import click
import logging
import requests
import sys

from ffua.graph import Graph,spantree,getLeafs
from ffua.hopglass import getDataFromHopGlass
from ffua.manifest import parse_manifest
from ffua.mechanism import outerToInnerUpgrade, miauEnforce

def htAllowNode(node,output):
    print(f"# { node['nodeinfo']['hostname'] }",file=output)
    print(f"# { node['nodeinfo']['software']['firmware']['release'] }",file=output)
    if "autoupdater" in node['nodeinfo']['software']:
        if "branch" in node['nodeinfo']['software']['autoupdater']:
            print(f"# { node['nodeinfo']['software']['autoupdater']['branch'] }",file=output)
    for address in node['nodeinfo']['network']['addresses']:
        print(f"allow from { address }",file=output)

def generateHtAccessRules(generator,output):
    
    print("order deny,allow",file=output)
    num = 0
    for nodedata in generator:
        try:
            htAllowNode(nodedata,output)
            num = num + 1
        except:
            pass
    print("deny from all",file=output)
    print(f"#Allowed nodes: { num }",file=output)

@click.group()
@click.option('--startnode','-s',type=click.STRING,default="deadbecccc00",help="Node Id of the network center",multiple=True)
@click.option('--hopglass',type=click.STRING,default="https://hopglass.freifunk.in-kiel.de/",help="URL to hopglass instance")
@click.option('--output','-o',type=click.File(mode='w'),default=sys.stdout)
@click.pass_context
def cli(ctx,startnode,hopglass,output):
    graph = getDataFromHopGlass(hopglass)
    if len(startnode) > 1:
        """
        Construct virtual node and add a link to all startnodes.
        """
        startident = graph.numNodes()
        graph.setNodeIdent(startident,"_VIRTUAL")
        for sn in startnode:
            num = 0
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
