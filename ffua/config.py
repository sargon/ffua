import attr
import ipaddress
import json
from pathlib import Path

from ffua.manifest import parse_manifest
from ffua.branch import recurse_firmware_directory

@attr.s
class Config:
    hopglass = attr.ib(default="http://localhost:4000/")
    startnodes = attr.ib(factory=list)
    firmware_path = attr.ib(default=Path("/opt/firmware/"))
    branches = attr.ib(factory=dict)
    incompatible = attr.ib(factory=dict)
    nets = attr.ib(factory=list)

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
            branches = dict(recurse_firmware_directory(self.firmware_path))
        if "branches" not in config:
            if "stable" in branches:
                self.branches["stable"] = branches["stable"]
        else:
            for branch in config['branches']:
                if branch in branches:
                    self.branches[branch] = branches[branch]
                else:
                    raise Exception(f"Configured branch '{branch}' not found")
        if "incompatible" in config:
            """
            Build up list of incompatible branches.
            """
            self.incompatible = config['incompatible']
            for branch in branches:
                if branch not in self.incompatible:
                    self.incompatible[branch] = list()
        if "nets" in config:
            map(ipaddress.ip_network, config["nets"])
            self.nets = config["nets"]


    def get_branch(self,branch):
        return self.branches[branch]
