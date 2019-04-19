import attr
from pathlib import Path

from ffua.manifest import parse_manifest,Manifest

@attr.s
class Branch:
    path = attr.ib(type=Path)
    has_factory = attr.ib(type=bool)
    sysupgrade_manifest = attr.ib(type=Manifest,default=None)

    def getSysupgradePath(self):
        return self.path / "sysupgrade"

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
        yield (branch_directory.name,Branch.from_path(branch_directory))

