# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator

import pytest
from disce.storage.base import AbstractStorage
from disce.storage.local import LocalStorage

from disce_tests.injected.storage.base import clear_storage


@pytest.fixture(autouse=True)
def storage() -> Generator[AbstractStorage]:
    with clear_storage(LocalStorage()) as storage:
        yield storage
