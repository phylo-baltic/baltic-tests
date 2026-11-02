"""Checks run on every tree file listed in a ``trees/*/manifest.yaml``."""

import math

import pytest

import baltic as bt
from treefiles import EXPECTED_FILE, MANIFEST_FILE, TREES_DIR, discover, summarize


def test_manifests_cover_tree_files():
    listed = {case.path for case in discover()}
    for directory in sorted(p for p in TREES_DIR.iterdir() if p.is_dir()):
        on_disk = {p for p in directory.iterdir() if p.name not in (MANIFEST_FILE, EXPECTED_FILE)}
        assert on_disk - listed == set(), f"files in {directory.name}/ missing from its {MANIFEST_FILE}"
    missing = sorted(str(p) for p in listed if not p.exists())
    assert missing == [], "manifest entries point at files that do not exist"


def test_summary_matches_expected(tree_case, tree):
    if tree_case.expect is None:
        pytest.fail(f"no expected values for {tree_case.id}; run: python tools/snapshot.py {tree_case.id}")
    actual = summarize(tree)
    for key, expected in tree_case.expect.items():
        assert key in actual, f"{key} no longer reported by summarize()"
        if isinstance(expected, float):
            assert actual[key] == pytest.approx(expected, rel=tree_case.rtol), key
        else:
            assert actual[key] == expected, key


def test_parent_child_links(tree):
    assert tree.root.parent is not None, "root should hang off the placeholder parent node"
    for k in tree.Objects:
        assert k.parent is not None
        if k.is_node():
            for child in k.children:
                assert child.parent is k


def test_heights_add_up(tree):
    for k in tree.Objects:
        if k is tree.root:
            continue
        assert math.isclose(k.height, k.parent.height + k.length, rel_tol=1e-9, abs_tol=1e-9), k.index


def test_tip_names_unique(tree):
    names = [k.name for k in tree.get_external()]
    assert len(names) == len(set(names))


def test_absolute_times_within_sampling(tree):
    if tree.mostRecent is None:
        pytest.skip("tree has no absolute time")
    for k in tree.Objects:
        assert k.absoluteTime <= tree.mostRecent + 1e-9
    assert tree.root.absoluteTime == pytest.approx(tree.mostRecent - tree.treeHeight, abs=1e-6)


def test_newick_round_trip(tree_case, tree):
    if any(isinstance(k, bt.Reticulation) for k in tree.Objects):
        pytest.skip("to_string does not write reticulations")
    reparsed = bt.make_tree(tree.to_string(traits=[]), treeType=tree_case.kwargs["treeType"])
    original = summarize(tree)
    again = summarize(reparsed)
    assert sorted(k.name for k in reparsed.get_external()) == sorted(k.name for k in tree.get_external())
    for key in ("numLeaves", "numNodes", "strictlyBifurcating", "multitypeTree"):
        assert again[key] == original[key], key
    for key in ("treeHeight", "treeLength"):
        assert again[key] == pytest.approx(original[key], rel=1e-9, abs=1e-12), key
