#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screens of the application."""

from pathlib import Path

__all__ = sorted(file.stem for file in Path(__file__).parent.glob("*.py") if file.stem != "__init__")  # noqa: PLE0605
