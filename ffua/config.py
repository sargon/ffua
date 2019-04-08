import attr
import json
from pathlib import Path

from ffua.manifest import parse_manifest

@attr.s
class Config:
    hopglass = attr.ib(default="http://localhost:4000/")
    startnodes = attr.ib(factory=list)
    firmware_path = attr.ib(default=Path("/opt/firmware/"))
    branches = attr.ib(factory=list)

    def load(self,config_file):
        config = json.load(config_file)
        if not isinstance(config,dict):
            raise Exception("Config is malformed, expected dict")
        if "hopglass" in config:
            self.hopglass = config['hopglass']
        if "startnodes" in config:
            self.startnodes = config['startnodes']
        else:
            raise Exception("Missing startnodes in config")
        if "firmware_path" in config:
            self.firmware_path = Path(config['firmware_path'])
        if "branches" not in config:
            self.branches['stable'] = parse_manifest(self.firmware_path / "stable" / "sysupgrade" / "stable.manifest")
        else:
            for branch in config['branches']:
                self.branches[branch] = parse_manifest(self.firmware_path / branch / "sysupgrade" / f"{ branch }.manifest")


    def get_branch(self,branch):
        return self.branches[branch]
