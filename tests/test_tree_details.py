"""Hand-checked details of specific tree files, beyond the generic checks in test_tree_files.py.

Moved here from baltic's tests/testsuite.py, together with the files they use.
"""

import collections

import baltic as bt
from treefiles import TREES_DIR, open_text


def trait_counts(tree):
    """Number of traits on the root, and the distinct counts on other nodes and on tips."""
    tree.traverse_tree()
    nodes = {len(k.traits) for k in tree.Objects if k.is_node() and k is not tree.root}
    tips = {len(k.traits) for k in tree.Objects if k.is_leaf()}
    return len(tree.root.traits), nodes, tips


def test_beast1_trait_counts(load_tree):
    root, nodes, tips = trait_counts(load_tree("beast1/miniFluB.mcc.tree.gz"))

    assert root == 77
    assert nodes <= {77, 74, 71, 41}
    assert tips <= {76, 73, 70}


def test_beast2_trait_counts(load_tree):
    root, nodes, tips = trait_counts(load_tree("beast2/MERS.mcc.tree.gz"))

    assert root == 10
    assert nodes == {13}
    assert tips <= {9, 12}


def test_zika_newick_size_and_height(load_tree):
    tree = load_tree("raxml/zika.nwk.gz")

    assert len(tree.Objects) == 564
    assert round(max(k.height for k in tree.Objects), 4) == 0.0058


def test_zika_bootstrap_labels(load_tree):
    tree = load_tree("raxml/zika.nwk.gz")
    labels = [k.traits.get("label") for k in tree.get_internal() if k is not tree.root]

    assert all(label is not None and label.isdigit() for label in labels)


def test_treetime_nexus_and_newick_loaders_agree():
    path = TREES_DIR / "treetime" / "divergence_tree.nexus.gz"
    with open_text(path) as handle:
        from_nexus = bt.load_nexus(handle, treeType="divergence", absoluteTime=False)
    with open_text(path) as handle:
        from_newick = bt.load_newick(handle, treeType="divergence")

    assert len(from_nexus.get_external()) == 283
    assert sorted((k.name, k.length) for k in from_nexus.get_external()) == sorted(
        (k.name, k.length) for k in from_newick.get_external()
    )
    assert collections.Counter(len(k.traits) for k in from_nexus.Objects) == collections.Counter(
        len(k.traits) for k in from_newick.Objects
    )
