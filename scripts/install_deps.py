#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Install the dependencies of the project."""

import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    """Install the dependencies of the project."""
    target_dir = Path(__file__).parent.parent / "src/deps"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(exist_ok=True)
    with TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        subprocess.run(["npm", "install", "--no-save", "@pyscript/core", "pyodide"], check=False, cwd=temp_dir)
        shutil.copytree(temp_dir / "node_modules/@pyscript/core/dist", target_dir / "pyscript")
        (target_dir / "pyodide").mkdir()
        pyodide_source_dir = temp_dir / "node_modules/pyodide"
        for file in sorted([*pyodide_source_dir.glob("pyodide*"), pyodide_source_dir / "python_stdlib.zip"]):
            shutil.copyfile(file, target_dir / "pyodide" / file.name)


if __name__ == "__main__":
    main()
