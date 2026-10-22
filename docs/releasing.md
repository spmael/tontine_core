# Release Process

This project publishes Python distributions to PyPI from GitHub Actions. The
`Upload Python Package` workflow runs when a GitHub Release is published, checks
that the release tag matches the version in `pyproject.toml`, runs the test
suite, builds the wheel and source distribution, and publishes those files to
PyPI using trusted publishing.

> **Publishing warning:** Publishing a GitHub Release triggers publication to
> PyPI. PyPI releases cannot be overwritten or deleted to reuse the same
> version. Do not publish a release until its version, contents, and release
> notes have been reviewed.

## Prepare a release

1. **Merge the release changes to `main`.** Do not tag a feature branch. Confirm
   the intended source commit is present on `main` and the worktree is clean.
2. **Choose the next version.** Follow Semantic Versioning:
   - patch (`0.2.1`) for compatible fixes;
   - minor (`0.3.0`) for compatible functionality additions before `1.0.0`;
   - major (`1.0.0`) for the first stable API or a breaking release after 1.0.
   Before 1.0, document API changes clearly even when choosing a minor version.
3. **Update all version declarations together.** Set the version in
   `pyproject.toml`, `src/tontine/__init__.py`, and `BRD.md`; update the version
   assertion in `tests/test_import.py`; then run `uv lock` so `uv.lock` records
   the package version.
4. **Review the release contents.** Inspect the changes since the previous
   release tag. Confirm the public API, supported Python versions, dependency
   metadata, and documentation accurately describe the release. Write concise
   release notes covering notable additions, fixes, and any compatibility
   changes.
5. **Run release checks locally.**

   ```bash
   uv sync --locked
   uv run pytest
   uv run ruff check src tests
   uv run mypy src
   uv build
   ```

   Check that the wheel and source distribution in `dist/` have the intended
   version and contents. Do not commit generated distribution files.
6. **Commit and merge the release changes.** Ensure CI passes on the commit
   merged to `main`.
7. **Check the tag is unused.** Use `git tag --list 'v<version>'` and verify
   that the version has not already been released on PyPI.

## Publish

8. **Create and push the release tag on `main`.** Use the `v` prefix, for
   example:

   ```bash
   git switch main
   git pull --ff-only
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

   Replace `v0.2.0` with the selected version. Confirm the tag points to the
   intended, CI-verified commit.
9. **Create a GitHub Release for that tag.** Add the reviewed release notes, then
   publish the release. Publishing it starts the `Upload Python Package`
   workflow and publishes the built distributions to PyPI if its checks pass.
10. **Verify the outcome.** Confirm the workflow completed successfully, the
    exact version and files appear on PyPI, and installation metadata reports
    the expected version. If the workflow fails, investigate before retrying;
    do not try to reuse a version already published to PyPI.

## Current release preparation

The repository is being prepared for `0.2.0`. That version is not released
until a `v0.2.0` GitHub Release is published and the PyPI workflow succeeds.
