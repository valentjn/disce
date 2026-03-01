# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pathlib import Path

import disce
import pytest

from disce_tests.selenium.servers import server_url  # noqa: F401
from disce_tests.selenium.web_drivers import driver_path, general_web_driver, web_driver  # noqa: F401


@pytest.fixture(scope="session")
def src_dir() -> Path:
    return Path(disce.__file__).parent.parent.parent
