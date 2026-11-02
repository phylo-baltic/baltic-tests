from pathlib import Path

import pytest

import baltic as bt
from treefiles import discover, load

TREE_CASES = discover()


def pytest_report_header(config):
    version = getattr(bt, "__version__", "unknown version")
    return f"baltic: {version} from {Path(bt.__file__).parent}"


def pytest_generate_tests(metafunc):
    """Parametrize any test taking ``tree_case`` over every manifest entry."""
    if "tree_case" not in metafunc.fixturenames:
        return
    params = []
    for case in TREE_CASES:
        marks = [pytest.mark.slow] if case.slow else []
        if case.xfail:
            marks.append(pytest.mark.xfail(reason=case.xfail, strict=True))
        params.append(pytest.param(case, id=case.id, marks=marks))
    metafunc.parametrize("tree_case", params)


@pytest.fixture(scope="session")
def tree_cache():
    return {}


@pytest.fixture
def load_tree(tree_cache):
    """Return a function that loads a manifest entry by id, e.g. ``"beast1/miniFluB.mcc.tree.gz"``.

    Trees are parsed once per session and shared between tests, so tests must not
    modify them. A file that fails to load is not re-parsed for every test.
    """
    cases = {case.id: case for case in TREE_CASES}

    def _load(case_id):
        if case_id not in tree_cache:
            try:
                tree_cache[case_id] = load(cases[case_id])
            except Exception as error:
                tree_cache[case_id] = error
        cached = tree_cache[case_id]
        if isinstance(cached, Exception):
            raise cached
        return cached

    return _load


@pytest.fixture
def tree(tree_case, load_tree):
    """The loaded tree for ``tree_case`` (shared; see ``load_tree``)."""
    return load_tree(tree_case.id)
