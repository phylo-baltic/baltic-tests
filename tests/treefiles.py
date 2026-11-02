"""Discovery, loading and summarising of the tree files under ``trees/``.

Each ``trees/<program>/manifest.yaml`` is written by hand and lists the files in
that directory and how to load them with baltic. The matching ``expected.yaml``
holds the summary values a correct load should produce and is written by
``tools/snapshot.py``.
"""

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

import baltic as bt

TREES_DIR = Path(__file__).resolve().parent.parent / "trees"

MANIFEST_FILE = "manifest.yaml"
EXPECTED_FILE = "expected.yaml"
LOADERS = ("newick", "nexus", "json")
ENTRY_KEYS = {"file", "loader", "kwargs", "description", "source", "slow", "rtol", "xfail"}


@dataclass(frozen=True)
class TreeCase:
    program: str
    path: Path
    loader: str
    kwargs: dict = field(default_factory=dict)
    description: str = ""
    source: str = ""
    slow: bool = False
    rtol: float = 1e-9
    expect: dict | None = None
    xfail: str | None = None

    @property
    def id(self):
        return f"{self.program}/{self.path.name}"


def read_expected(directory):
    path = directory / EXPECTED_FILE
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def read_manifest(manifest):
    program = manifest.parent.name
    entries = yaml.safe_load(manifest.read_text(encoding="utf-8")) or []
    expected = read_expected(manifest.parent)
    cases = []
    for entry in entries:
        unknown = set(entry) - ENTRY_KEYS
        if unknown:
            raise ValueError(f"{manifest}: unknown keys {sorted(unknown)} in entry for {entry.get('file')}")
        if entry["loader"] not in LOADERS:
            raise ValueError(f"{manifest}: loader must be one of {LOADERS}, got {entry['loader']!r}")
        cases.append(
            TreeCase(
                program=program,
                path=manifest.parent / entry["file"],
                loader=entry["loader"],
                kwargs=entry.get("kwargs") or {},
                description=entry.get("description", ""),
                source=entry.get("source", ""),
                slow=entry.get("slow", False),
                rtol=entry.get("rtol", 1e-9),
                expect=expected.get(entry["file"]),
                xfail=entry.get("xfail"),
            )
        )
    return cases


def discover(trees_dir=TREES_DIR):
    cases = []
    for manifest in sorted(trees_dir.glob(f"*/{MANIFEST_FILE}")):
        cases.extend(read_manifest(manifest))
    return cases


def open_text(path):
    """Open a tree file as text, decompressing ``.gz`` files transparently."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, encoding="utf-8")


def load(case):
    """Load a :class:`TreeCase` with baltic and return the tree."""
    with open_text(case.path) as handle:
        if case.loader == "newick":
            return bt.load_newick(handle, **case.kwargs)
        if case.loader == "nexus":
            return bt.load_nexus(handle, **case.kwargs)
        tree, _meta = bt.load_JSON(json.load(handle), **case.kwargs)
        return tree


def summarize(tree):
    """Summary values compared against a manifest's ``expect`` block."""
    summary = tree.treeStatsDict()
    summary["numReticulations"] = sum(1 for k in tree.Objects if isinstance(k, bt.Reticulation))
    summary["numTraitNames"] = len({key for k in tree.Objects for key in k.traits})
    if tree.mostRecent is not None:
        summary["mostRecent"] = tree.mostRecent
    return summary
