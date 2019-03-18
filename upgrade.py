#!/usr/bin/env python3

import click
from datetime import datetime, timedelta
import logging
import requests

from ffua.graph import Graph,spantree,getLeafs
from ffua.hopglass import getDataFromHopGlass
from ffua.manifest import parse_manifest


def htAllowNode(node):
    print(f"# { node['nodeinfo']['hostname'] }")
    print(f"# { node['nodeinfo']['software']['firmware']['release'] }")
    if "autoupdater" in node['nodeinfo']['software']:
        if "branch" in node['nodeinfo']['software']['autoupdater']:
            print(f"# { node['nodeinfo']['software']['autoupdater']['branch'] }")
    for address in node['nodeinfo']['network']['addresses']:
        print(f"allow from { address }")

def generateHtAccessRules(generator):
    
    print("order deny,allow")
    num = 0
    for nodedata in generator:
        try:
            htAllowNode(nodedata)
            num = num + 1
        except:
            pass
    print("deny from all")
    print(f"#Allowed nodes: { num }")

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
                branch = node['nodeinfo']['software']['autoupdater']['branch']
                if branch != targetbranch:
                    yield nodedata
        except:
            pass

@click.group()
@click.option('--startnode','-s',type=click.STRING,default="deadbecccc00",help="Node Id of the network center",multiple=True)
@click.option('--hopglass',type=click.STRING,default="https://hopglass.freifunk.in-kiel.de/",help="URL to hopglass instance")
@click.pass_context
def cli(ctx,startnode,hopglass):
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

@cli.command(name="miauEnforce")
@click.option("--min-distance","-d",type=click.INT,default=2)
@click.argument("manifest_path",type=click.Path(exists=True,dir_okay=False))
@click.pass_context
def miau(ctx,min_distance,manifest_path):
    manifest = parse_manifest(manifest_path)
    firmware_version = manifest.getFirmwareVersion().pop()
    firmware_branch = manifest.branch
    print(f"#Tracking firmware version: { firmware_version }")
    graph = ctx.obj['graph']
    tree = ctx.obj['tree']
    if ctx.obj['virtual_rootnode']:
        min_distance += 1
    generator = miauEnforce(graph,tree,firmware_branch,firmware_version,min_distance)
    generateHtAccessRules(generator)
    

@cli.command(name="outerToInnerUpgrade")
@click.pass_context
def otiu(ctx):
    graph = ctx.obj['graph']
    tree = ctx.obj['tree']
    generator = outerToInnerUpgrade(graph,tree)
    generateHtAccessRules(generator)

if __name__ == "__main__":
    cli(obj={})
