#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from pathlib import Path

import disce
import pytest
from disce.main import compute_source_hash, set_up_logging


def test_set_up_logging(capsys: pytest.CaptureFixture[str]) -> None:
    root_logger = logging.getLogger()
    handlers = root_logger.handlers
    root_logger.handlers = []
    try:
        set_up_logging()
        logging.getLogger("disce.main").debug("message")
        capture_result = capsys.readouterr()
        assert capture_result.out == "disce.main: message\n"
    finally:
        root_logger.handlers = handlers


def test_compute_source_hash_without_change() -> None:
    assert compute_source_hash() == compute_source_hash()


def test_compute_source_hash_with_change() -> None:
    source_hash = compute_source_hash()
    path = Path(disce.__file__).with_name("non_existent.py")
    path.touch()
    try:
        assert compute_source_hash() != source_hash
    finally:
        path.unlink()
