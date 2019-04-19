from ffua.branch import recurse_firmware_directory
from pathlib import Path

def test_branch_load():
    branches = dict(recurse_firmware_directory(Path("./firmware/")))
    print(branches)
    assert "stable" in branches
    assert "nightly" in branches
