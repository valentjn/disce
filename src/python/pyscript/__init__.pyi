#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")

document: Any
when: Callable[[str, str], Callable[[Callable[_P, _R]], Callable[_P, _R]]]
window: Any
