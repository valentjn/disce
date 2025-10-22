#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import gzip
import logging
from base64 import b64encode
from pathlib import Path
from time import sleep

import pytest
from disce.main import set_up_logging

_logger = logging.getLogger(__name__)


def main() -> None:
    set_up_logging()
    _logger.info("Disce started")
    sleep(1.0)
    _logger.info("running injected tests")
    exit_code = pytest.main(
        [
            "--color=yes",
            "--cov=disce",
            "--cov-report=term-missing",
            "--pythonwarnings=error",
            "--pythonwarnings=ignore:Couldn't import C tracer",
            "--log-format=%(name)s:%(levelname)s - %(message)s",
            "--log-level=INFO",
            "--verbose",
            "--verbose",
            "disce_tests/injected",
        ]
    )
    _logger.info(
        ".coverage file of injected tests: %s", b64encode(gzip.compress(Path(".coverage").read_bytes())).decode()
    )
    _logger.info("finished injected tests, exit code: %d", exit_code)
