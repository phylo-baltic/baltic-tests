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
def tree(tree_case, tree_cache):
    """The loaded tree for ``tree_case``, parsed once per session.

    Tests share the cached object, so they must not modify it. A file that fails
    to load is not re-parsed for every test that uses it.
    """
    if tree_case.id not in tree_cache:
        try:
            tree_cache[tree_case.id] = load(tree_case)
        except Exception as error:
            tree_cache[tree_case.id] = error
    cached = tree_cache[tree_case.id]
    if isinstance(cached, Exception):
        raise cached
    return cached
