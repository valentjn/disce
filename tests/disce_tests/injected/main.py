#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from time import sleep

import pytest
from disce.main import main as disce_main

_logger = logging.getLogger(__name__)


def main() -> None:
    disce_main()
    sleep(1.0)
    _logger.info("running injected tests")
    exit_code = pytest.main(
        [
            "--color=yes",
            "--pythonwarnings=error",
            "--log-format=%(name)s:%(levelname)s - %(message)s",
            "--log-level=INFO",
            "--verbose",
            "--verbose",
            "disce_tests/injected",
        ]
    )
    _logger.info("finished injected tests, exit code: %d", exit_code)
