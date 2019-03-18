import attr
from datetime import datetime
from pathlib import Path

@attr.s
class Manifest:
    path = attr.ib(type=Path)
    branch = attr.ib(type=str,default=None)
    priority = attr.ib(type=int,default=None)
    targets = attr.ib(factory=dict)

    #date = attr.ib(type=datetime,factory=datetime)

    def getFirmwareVersion(self):
        versions = dict()
        for target in self.targets.values():
            versions[target.version] = None
        return list(versions.keys())

@attr.s
class Firmware:
    target  = attr.ib(type=str)
    version = attr.ib(type=str,default=None)
    sha256  = attr.ib(type=str,default=None)
    sha512  = attr.ib(type=str,default=None)
    filename = attr.ib(type=str,default=None)
    filesize = attr.ib(type=str,default=None)

def parse_manifest(manifest_path):
    manifest = Manifest(Path(manifest_path))

    def getFirmware(target):
        if target in manifest.targets:
            firmware = manifest.targets[target]
        else:
            firmware = Firmware(target)
            manifest.targets[target] = firmware
        return firmware

    with manifest.path.open('r') as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("BRANCH="):
                manifest.branch = line[7:]
            elif line.startswith("PRIORITY="):
                manifest.priority = int(line[9:])
            elif line.startswith("DATE="):
                # manifest.date = ...
                pass
            else:
                parts = line.split(" ")
                if len(parts) >= 4:
                    firmware = getFirmware(parts[0])
                    firmware.version = parts[1]
                    if len(parts[2]) == 64:
                        firmware.sha256 = parts[2]
                    elif len(parts[2]) == 128:
                        firmware.sha512 = parts[2]
                if len(parts) == 4:
                    firmware.filename = parts[3]
                if len(parts) == 5:
                    firmware.filesize = parts[3]
                    firmware.filename = parts[4]

    return manifest
