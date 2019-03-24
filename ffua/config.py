import attr
import json

@attr.s
class Config:
    hopglass = attr.ib(default="http://localhost:4000/")
    startnodes = attr.ib(factory=list)

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
