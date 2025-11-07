#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest


@pytest.fixture
def furigana_string() -> str:
    return 2 * "\u6f22[\u304b\u3093]\u5b57[\u3058]\u30c6\u30b9\u30c8"


@pytest.fixture
def furigana_stripped() -> str:
    return 2 * "\u6f22\u5b57\u30c6\u30b9\u30c8"


@pytest.fixture
def furigana_html() -> str:
    return 2 * (
        "<ruby>\u6f22<rp>\uff08</rp><rt>\u304b\u3093</rt><rp>\uff09</rp></ruby>"
        "<ruby>\u5b57<rp>\uff08</rp><rt>\u3058</rt><rp>\uff09</rp></ruby>\u30c6\u30b9\u30c8"
    )
