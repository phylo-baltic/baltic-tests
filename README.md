# baltic-tests

Heavy-duty tests for [baltic](https://github.com/evogytis/baltic): regular
Python tests, plus real tree files written by phylogenetic programs (BEAST,
TreeTime, IQ-TREE, Nextstrain, ...). These are kept out of the main repository
so it stays small.

## Layout

```
tests/                     pytest tests
  conftest.py              parametrises tests over every tree file; caches parsed trees
  treefiles.py             manifest reading, loading and summarising helpers
  test_tree_files.py       checks run on every tree file
  test_tree_details.py     hand-checked details of specific files (moved from baltic)
trees/<program>/           one directory per program that produced the files
  *.gz                     gzip-compressed tree files
  manifest.yaml            hand-written: how to load each file, and where it came from
  expected.yaml            generated: summary values a correct load produces
tools/snapshot.py          (re)generates expected.yaml
.github/workflows/tests.yml
```

## Running locally

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ../baltic -r requirements.txt   # .venv/bin/python on macOS/Linux
.venv/Scripts/python -m pytest                  # everything
.venv/Scripts/python -m pytest -m "not slow"    # skip the big files
.venv/Scripts/python -m pytest -k beast2        # one program
```

The pytest header shows which baltic is under test, so you can check the
editable install is picked up.

## What gets checked for each tree file

- **Summary vs. `expected.yaml`**: tip, node and object counts, tree height
  and length, topology flags, number of reticulations, number of distinct trait
  names, and `mostRecent`.
- **Structure**: parent/child links agree, every branch's height equals its
  parent's height plus its length, tip names are unique, and absolute times
  don't go past `mostRecent`.
- **Round trip**: `to_string()` then `make_tree()` gives the same tips,
  topology counts, height and length.

Each file is parsed once per session, so a file that fails to parse shows up
as errors in every test that uses it.

## Adding a tree file

1. Compress it into the program's directory (make one if needed):
   `gzip -k -9 my.tree && mv my.tree.gz trees/beast2/`. Uncompressed files
   also work, but keep each file under GitHub's 100 MB limit.
2. Add an entry to that directory's `manifest.yaml`:

   ```yaml
   - file: my.tree.gz
     description: What it is and why it is interesting (e.g. an unusual annotation).
     source: Where it came from (paper, tutorial, program version).
     loader: nexus          # newick | nexus | json
     kwargs: {treeType: time, tipRegex: '_([0-9-]+)$'}   # passed to the baltic loader
     slow: true             # optional: large file, deselected by -m "not slow"
     rtol: 1.0e-9           # optional: relative tolerance for float comparisons
     xfail: "reason"        # optional: known baltic bug; the test fails if it starts passing
   ```

3. Record its expected values, then **check them by hand** (tip count, tree
   height, dates). They are a snapshot of what the installed baltic produces,
   so a parsing bug would be recorded as correct:

   ```bash
   python tools/snapshot.py beast2/my.tree
   git diff trees/
   ```

If a baltic change legitimately alters a summary, rerun the snapshot for the
affected files and commit the `expected.yaml` diff with an explanation.

Other tests (not tied to a tree file) go in `tests/test_*.py` as usual. Use
`treefiles.TREES_DIR` to find data, and mark expensive tests with
`@pytest.mark.slow`.

## Continuous integration

`.github/workflows/tests.yml` installs baltic from a checkout and runs pytest
on Python 3.10–3.13 (Ubuntu), plus 3.13 on macOS and Windows. It runs:

- on pushes and pull requests to this repository, against baltic's default
  branch;
- nightly, to catch regressions on baltic's default branch;
- on demand from the Actions tab, with any baltic repository and ref;
- from the baltic repository, as a reusable workflow. Add this to a workflow
  there to test every push and PR:

  ```yaml
  jobs:
    heavy-tests:
      uses: phylo-baltic/baltic-tests/.github/workflows/tests.yml@main
      with:
        baltic-repository: ${{ github.repository }}
        baltic-ref: ${{ github.sha }}
  ```

  This needs baltic-tests to be public, because the caller is in a different
  account.

## License

The code in this repository is released under the [MIT License](LICENSE). The
tree files were produced from third-party data and published analyses; each
file's origin is recorded in the `source` field of its `manifest.yaml` entry.
