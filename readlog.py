#!/usr/bin/env python3

import attr
import click
from enum import auto,Enum
import logging
from pathlib import Path

import ffua

class RequestType(Enum):
    Firmware = auto()
    Manifest = auto()

@attr.s(auto_attribs=True)
class Request:
    type: RequestType
    source: str
    method: str
    branch: str
    filename: str

def parse_logfile(logfile,*args,**kargs):
    for line in logfile.readlines():
        yield parse_logline(line,*args,**kargs)

def parse_logline(line,with_manifest = False):
    try:
        fields = line.split()
        if len(fields) < 5:
            return
        address = fields[0]
        method = fields[1][1:]
        path = Path(fields[2])
        status = int(fields[4])
        if method == "GET" and status == 200:
            if path.parent.name == "sysupgrade":
                branch = path.parent.parent.name
                if path.suffix == ".manifest":
                    if with_manifest:
                        return Request(RequestType.Manifest,address,method,branch,path.name)
                else:
                    filename = path.name
                    return Request(RequestType.Firmware,address,method,branch,path.name)

    except:
        return None

@click.group()
@click.option('--config','-c','config_file',type=click.File(mode='r'),prompt=True)
@click.pass_context
def cli(ctx,config_file):
    config = ffua.config.Config()
    config.load(config_file) 
    ctx.obj['config'] =  config
    logging.basicConfig(level=logging.WARNING)


@cli.command()
@click.option("--with-manifest/--without-manifest",default=False,help="Output manifest requests")
@click.argument("logfiles",type=click.File(mode='r+'),nargs=-1)
def parse(with_manifest,logfiles):
    print("Start reading")
    for logfile in logfiles:
        for request in parse_logfile(logfile,with_manifest):
            if request is not None:
                print(request.source,request.type,request.branch,request.filename)

def find_node_from_address(graph,address):
    for node in graph.getNodes():
        nodedata = graph.getNode(node).data
        if nodedata is None:
            continue
        if 'nodeinfo' in nodedata:
            if 'network' in nodedata['nodeinfo']:
                if 'addresses' in nodedata['nodeinfo']['network']:
                    if address in nodedata['nodeinfo']['network']['addresses']:
                        return node
    return None

@cli.command()
@click.argument("logfiles",type=click.File(mode='r+'),nargs=-1)
@click.pass_context
def verify(ctx,logfiles):
    config = ctx.obj['config']
    logging.info("Get graph data")
    graph = ffua.hopglass.getDataFromHopGlass(config.hopglass)
    graph_center = ffua.graph.addVirtualNode(graph,config.startnodes)
    # Add magic starting node
    # Remove none connected nodes from graph
    for logfile in logfiles:
        for request in parse_logfile(logfile):
            if request is not None:
                nodeid = find_node_from_address(graph,request.source)
                if nodeid is None:
                    logging.warning(f"Node for {request.source} not found")
                else:
                    node = graph.getNode(nodeid)
                    hostname = "<?>"
                    if 'hostname' in node.data['nodeinfo']:
                        hostname = node.data['nodeinfo']['hostname']
                    # delete node from graph
                    logging.info(f"Upgrade {request.branch} on {nodeid}:{hostname}")
                    graph.removeNode(nodeid)
                    # check if graph is still connected
                    # if check fails, report disconnected nodes
        

if __name__ == "__main__":
    cli(obj=dict())
