#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from disce.models.configs import Configuration


class TestConfiguration:
    @staticmethod
    def test_get_storage_key() -> None:
        assert Configuration.get_storage_key(None) == "configuration"
