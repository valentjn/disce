#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from time import sleep

import pytest
from disce.storage.local import LocalStorage


@pytest.fixture(autouse=True)
def wait() -> None:
    # sleep a bit before every test to reduce the chance of output being written by the injected tests while the output
    # capture is disabled by the calling test
    sleep(0.1)


@pytest.fixture(autouse=True)
def storage() -> Generator[LocalStorage]:
    storage = LocalStorage()
    yield storage
    storage.clear()
