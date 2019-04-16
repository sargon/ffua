#!/usr/bin/env python3

import click
import attr
from pathlib import Path
from enum import auto,Enum

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
    ctx.obj['config'] = ffua.config.Config(config_file)


@cli.command()
@click.option("--with-manifest/--without-manifest",default=False,help="Output manifest requests")
@click.argument("logfiles",type=click.File(mode='r+'),nargs=-1)
def parse(with_manifest,logfiles):
    print("Start reading")
    for logfile in logfiles:
        for request in parse_logfile(logfile,with_manifest):
            if request is not None:
                print(request.source,request.type,request.branch,request.filename)

@cli.command()
@click.argument("logfiles",type=click.File(mode='r+'),nargs=-1)
@click.pass_context
def verify(logfiles):
    graph = ffua.graph.getDataFromHopGlass(hopglass)


if __name__ == "__main__":
    cli(obj=dict())
