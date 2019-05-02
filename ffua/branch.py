import attr
import logging
from pathlib import Path

from ffua.manifest import Manifest

@attr.s
class Branch:
    path = attr.ib(type=Path)
    has_factory = attr.ib(type=bool)
    manifest = attr.ib(type=Manifest,default=None)

    def getSysupgradePath(self):
        return self.path / "sysupgrade"

    def getManifest(self):
        return self.manifest

    def getFirmwareVersion(self):
        return self.manifest.getFirmwareVersion()

    @classmethod
    def from_path(cls,path):
        # The important stuff
        sysupgrade_path = path / "sysupgrade"
        if not sysupgrade_path.is_dir():
            raise Exception("No valid branch directory - missing sysupgrade path.")
        manifest_path = sysupgrade_path / (path.name + ".manifest")
        if not manifest_path.is_file():
            raise Exception("No valid branch directory - missing sysupgrade manifest")
        manifest = Manifest.from_path(manifest_path)
        # The goodies
        factory_path = path / "factory"
        has_factory = factory_path.is_dir()
        # GoGoGo
        return cls(path,has_factory,manifest)


def recurse_firmware_directory(firmware_path: Path):
    for branch_directory in firmware_path.iterdir():
        try:
            yield (branch_directory.name,Branch.from_path(branch_directory))
        except Exception as e:
            logging.exception(e)

