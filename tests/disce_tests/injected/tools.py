#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import pytest
from disce.pyscript import Element
from disce.screens.base import AbstractScreen
from pyscript import document, window


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


def assert_hidden(obj: Element | AbstractScreen) -> None:
    assert get_style(obj).display == "none"


def assert_visible(obj: Element | AbstractScreen) -> None:
    assert get_style(obj).display != "none"


def get_style(obj: Element | AbstractScreen) -> Any:  # noqa: ANN401
    if isinstance(obj, AbstractScreen):
        obj = obj.element
    return window.getComputedStyle(obj)
