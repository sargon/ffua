import attr
import logging

@attr.s
class NodeMetaData:
    ident = attr.ib(type=str)
    raw = attr.ib(factory=dict)

    def hasMetaData(self):
        return len(self.raw) > 0

    def isOnline(self):
        try:
            return self.raw['nodeinfo']['flags']['online']
        except:
            return False

    def getBranch(self):
        try:
            return self.raw['nodeinfo']['software']['autoupdater']['branch']
        except:
            logging.error(f"Node { self.ident } has no Branch")
            return None

    def getFirmwareVersion(self):
        try:
            return self.raw['nodeinfo']['software']['firmware']['release']
        except:
            return None

    def getHostname(self):
        try:
            return self.raw['nodeinfo']['hostname']
        except:
            logging.error(f"Node { self.ident } has no Hostname")
            return None

    def getAddresses(self):
        try:
            return self.raw['nodeinfo']['network']['addresses']
        except:
            logging.error(f"Node { self.ident } has addresses")
            return list()

    def getLastSeen(self):
        try:
          return datetime.strptime(self.raw['lastseen'][0:18],"%Y-%m-%dT%H:%M:%S")
        except:
            logging.error(f"Node { self.ident } has no lastseen value")
            return None
