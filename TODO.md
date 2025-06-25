# TODO List for twat-labs Enhancement

This file tracks tasks to improve the `twat-labs` project.

## Phase 1: Initial Setup & Fixes (Completed)

-   [x] Create `PLAN.md`.
-   [x] Create `TODO.md` (this file).
-   [x] Fix `ruff` linting error in `src/twat_labs/__init__.py` (remove unused `importlib.metadata`).
-   [x] Fix `mypy` type error in `tests/test_twat_labs.py` (add `-> None` return type annotation to `test_version`).
-   [x] Rename `LOG.md` to `CHANGELOG.md` and update its structure.
-   [x] Update `cleanup.py` to use `CHANGELOG.md` instead of `LOG.md` in `REQUIRED_FILES`.
-   [x] Fix `repomix` call in `cleanup.py` to use `npx repomix`.
-   [x] Run `python cleanup.py update` and review its output to ensure all initial fixes are integrated and checks pass.

## Phase 2: Codebase Understanding and Refinement (Current)

-   [x] Understand the core purpose of `twat-labs` and its relation to `twat-fs` (mentioned in `.cursor/rules/0project.mdc`).
-   [ ] Review `src/twat_labs/__init__.py` for any necessary improvements or placeholder code. What should this plugin actually *do*? This will likely require user input or further clues.
-   [ ] Review `cleanup.py` script:
    -   Investigate why `__pycache__` directories appeared in `tree` output in `CLEANUP.txt` despite `.gitignore` and script's ignore patterns. Add `-I "__pycache__"` to the `tree` command if necessary.
    -   Consider if `cleanup.py` should manage the `git checkout` to a specific branch if `detached HEAD` is a recurring issue.
-   [ ] Review `README.md`: It's very sparse. Expand it once the project purpose is clear.

## Phase 3: Functionality Review and Enhancement

-   [ ] (To be populated after codebase understanding)

## Phase 4: Testing and Quality Assurance

-   [ ] Review `tests/test_twat_labs.py`: `test_version` is a good start, but more substantial tests will be needed once functionality is defined.

## Phase 5: Documentation Overhaul

-   [ ] Ensure `.cursor/rules/0project.mdc` accurately reflects the project as it evolves.
-   [ ] Update `CHANGELOG.md` with entries for work done in this phase.

## Phase 6: Build and CI/CD Pipeline Verification

-   [ ] Check `pyproject.toml` dependencies: Are `twat>=1.8.1` and other dev dependencies appropriate and up-to-date?
-   [ ] **Crucial:** Investigate `VERSION.txt` (`v2.7.5`) vs. `CHANGELOG.md` (latest tag `v1.7.5`) vs. `hatch-vcs` (which should generate `src/twat_labs/__version__.py`).
    -   Determine the true source of versioning.
    -   Ensure `VERSION.txt` is either correctly updated by the build process, removed if redundant, or its role clarified.
    -   The `hatch-vcs` setup should mean manual updates to `VERSION.txt` or `__version__.py` are not needed if tags are used correctly.

## Ongoing Tasks:

-   [ ] Regularly update `PLAN.md` with progress and new insights.
-   [ ] Regularly update this `TODO.md` list.
-   [ ] Record all significant changes in `CHANGELOG.md`.
