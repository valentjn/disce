#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Update pyscript.toml to include all Disce files."""

from pathlib import Path

import tomlkit


def main() -> None:
    """Update pyscript.toml to include all Disce files."""
    python_dir = Path(__file__).parent.parent / "src/python"
    disce_files = sorted(entry for entry in (python_dir / "disce").rglob("*") if entry.is_file())
    pyscript_toml = python_dir / "pyscript.toml"
    config = tomlkit.parse(pyscript_toml.read_text())
    config["files"] = {str(file.relative_to(python_dir).as_posix()): "./disce/" for file in disce_files}
    pyscript_toml.write_text(tomlkit.dumps(config))


if __name__ == "__main__":
    main()
