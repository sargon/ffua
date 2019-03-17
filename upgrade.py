#!/usr/bin/env python3

import requests
import click
from datetime import datetime, timedelta
from ffua.graph import Graph,spantree,getLeafs
from ffua.hopglass import getDataFromHopGlass


def htAllowNode(node):
    print(f"# { node['nodeinfo']['hostname'] }")
    print(f"# { node['nodeinfo']['software']['firmware']['release'] }")
    if "autoupdater" in node['nodeinfo']['software']:
        if "branch" in node['nodeinfo']['software']['autoupdater']:
            print(f"# { node['nodeinfo']['software']['autoupdater']['branch'] }")
    for address in node['nodeinfo']['network']['addresses']:
        print(f"allow from { address }")

def outerToInnerUpgrade(graph,tree):
    """
    Allow updates only for the leafs of the spantree of the network graph.
    Except for the situation where every child of a node is inactive.
    """
    
    print("order allow,deny")
    for node in tree.getNodes():

        if tree.getNode(node).degree() == 1:
            nodedata = graph.getNodeData(node)
            htAllowNode(nodedata)
        else:
            childs_active = False
            for gchild,_ in tree.getOutEdges(node).items():
                child = graph.getNodeData(gchild)
                lastseen =  datetime.strptime(child['lastseen'][0:18],"%Y-%m-%dT%H:%M:%S")
                now = datetime.utcnow()
                if now - lastseen < timedelta(minutes=30):
                    childs_active = True
            if not childs_active:
                nodedata = graph.getNodeData(node)
                htAllowNode(nodedata)

    print("deny from all")
    print(f"#Tree leafs: { len(getLeafs(tree)) }")


def miauEnforce(graph,tree,targetversion,min_distance=2):
    """
    Enforce miau usage by allowing all nodes with distance less 
    equal to min_distance the update and every node already 
    running the right version.
    """

    print("order allow,deny")
    num = 0
    for node in tree.getNodes():
        distance = tree.getNodeData(node)
        nodedata = graph.getNodeData(node)
        try:
            if distance <= min_distance:
                htAllowNode(nodedata)
                num = num + 1
            elif distance > min_distance:
                version = nodedata['nodeinfo']['software']['firmware']['release']
                if version == targetversion:
                    htAllowNode(nodedata)
                    num = num + 1
        except:
            pass

    print("deny from all")
    print(f"#Allowed nodes: { num }")

@click.group()
@click.option('--startnode',type=click.STRING,default="deadbecccc00",help="Node Id of the network center")
@click.option('--hopglass',type=click.STRING,default="https://hopglass.freifunk.in-kiel.de/",help="URL to hopglass instance")
@click.pass_context
def cli(ctx,startnode,hopglass):
    graph = getDataFromHopGlass(hopglass)
    tree = spantree(graph,graph.getGraphIdentFromIdent(startnode))
    ctx.obj['graph'] = graph
    ctx.obj['tree'] = tree

@cli.command(name="miauEnforce")
@click.argument("firmware_version")
@click.pass_context
def miau(ctx,firmware_version):
    graph = ctx.obj['graph']
    tree = ctx.obj['tree']
    miauEnforce(graph,tree,firmware_version)

@cli.command(name="outerToInnerUpgrade")
@click.pass_context
def otiu(ctx):
    graph = ctx.obj['graph']
    tree = ctx.obj['tree']
    outerToInnerUpgrade(graph,tree)

if __name__ == "__main__":
    cli(obj={})
