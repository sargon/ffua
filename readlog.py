#!/usr/bin/env python3

import click
import attr
from pathlib import Path

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
                        print(address,"manifest",branch)
                else:
                    filename = path.name
                    print(address,"firmware",branch,filename)

    except:
        pass

@click.command()
@click.option("--with-manifest/--without-manifest",default=False,help="Output manifest requests")
@click.argument("logfiles",type=click.File(mode='r+'),nargs=-1)
def cli(with_manifest,logfiles):
    print("Start reading")
    while True:
        for logfile in logfiles:

            line = logfile.readline()
            if line is not None and len(line) > 0:
                parse_logline(line,with_manifest)
            else:
                exit(1)

if __name__ == "__main__":
    cli()
