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
@click.option("--debug/--no-debug",default=False,help="Debugging output")
@click.option('--config','-c','config_file',type=click.File(mode='r'),prompt=True)
@click.pass_context
def cli(ctx,debug,config_file):
    config = ffua.config.Config()
    config.load(config_file)
    ctx.obj['config'] =  config
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


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
        nodedata = graph.getNodeData(node)
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

    def getHostname(node_data):
        hostname = "<?>"
        try:
            hostname = node_data['nodeinfo']['hostname']
        finally:
            return hostname

    def getBranch(node_data):
        branch = "<?>"
        try:
            branch = node_data['nodeinfo']['software']['autoupdater']['branch']
        finally:
            return branch

    config = ctx.obj['config']
    logging.info("Get graph data")
    graph = ffua.hopglass.getDataFromHopGlass(config.hopglass)
    # Add magic starting node
    graph_center = ffua.graph.addVirtualNode(graph,config.startnodes)
    # Remove none connected nodes from graph
    print("Start verification process")
    success = True
    for logfile in logfiles:
        for request in parse_logfile(logfile):
            if request is not None:
                node_id = find_node_from_address(graph,request.source)
                if node_id is None:
                    logging.debug(f"Node for {request.source} not found")
                else:
                    node_data = graph.getNodeData(node_id)
                    # delete node from graph
                    logging.info(f"Upgrade {request.branch} on {node_id}:{ getHostname(node_data)}")
                    graph.removeNode(node_id)
                    # check if graph is still connected
                    components = ffua.graph.getComponents(graph)
                    if len(components) > 1:
                        logging.warning(f"Remove of ({getBranch(node_data)}) {node_id}:{ getHostname(node_data) } disconnects graph")
                        disconnected = filter(lambda component: graph_center not in component,components)
                        success = False
                        for dis_component in disconnected:
                            for dis_node_id in dis_component:
                                dis_node_data = graph.getNodeData(dis_node_id)
                                logging.warning(f"Disconnect ({getBranch(node_data)}) {dis_node_id}:{ getHostname(dis_node_data) }")
                                graph.removeNode(dis_node_id)

                    # if check fails, report disconnected nodes
    print("Verfication ended")
    if success:
        print("No graph split detected")
    else:
        print("WARNING: Graph split was detected")
    center_node = graph.getNode(graph_center)
    if graph.numNodes() > 1 + center_node.degree():
        print(f"There are { graph.numNodes() - 1 - center_node.degree() } nodes still in the graph")
        for node_id in graph.getNodes():
            if not center_node.isNeighbor(node_id) and node_id != graph_center:
                node = graph.getNode(node_id)
                if node.data is None:
                    print(node.ident)
                else:
                    print(f" Node ({getBranch(node.data)}) {node_id}:{ getHostname(node.data) }")


if __name__ == "__main__":
    cli(obj=dict())
