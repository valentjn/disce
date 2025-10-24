#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from contextlib import contextmanager

import pytest
from disce.pyscript import Element
from pyscript import document


@contextmanager
def insert_element(element: Element) -> Generator[Element]:
    document.body.appendChild(element)
    try:
        yield element
    finally:
        document.body.removeChild(element)


def print_signal(signal_name: str, capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest) -> None:
    with capsys.disabled():
        print(f"{request.node.nodeid}: {signal_name}")  # noqa: T201
