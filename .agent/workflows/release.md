---
description: How to release OpenMemX to PyPI
---

This workflow guides you through the process of releasing a new version of OpenMemX.

1. **Verify environment**
   Ensure you are in the project root and the virtual environment is active.
   // turbo
   ```bash
   source venv/bin/activate
   ```

2. **Run Pre-release Checks**
   Use the helper script to run tests, linting, and build validation.
   // turbo
   ```bash
   ./scripts/release.sh
   ```

3. **Update Version**
   If a version bump is needed, update it in `pyproject.toml`.
   Example: Update to `1.1.0`.
   // turbo
   ```bash
   ./scripts/release.sh 1.1.0
   ```

4. **Update Changelog**
   Manually edit `CHANGELOG.md` to document the changes in the new version.

5. **Commit and Tag**
   Commit the changes and create a git tag.
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: release 1.1.0"
   git tag v1.1.0
   ```

6. **Push to Origin**
   Push the commit and the tag to GitHub.
   ```bash
   git push origin main --tags
   ```

7. **Publish on GitHub**
   Go to GitHub and create a "Release" from the new tag. 
   The `Publish to PyPI` GitHub Action will automatically trigger and upload to PyPI using OIDC.
