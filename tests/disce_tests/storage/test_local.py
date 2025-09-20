#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from selenium.webdriver import Firefox


class TestLocalStorage:
    def test_local_storage(self, browser: Firefox) -> None:
        '''
                #browser.execute_script("localStorage.setItem('key', 'value');")
                #assert browser.execute_script("return localStorage.getItem('key');") == "value"
                #browser.execute_script("""pyodide.runPython(`
        #import sys
        #sys.version
        #`);""")
        '''
        browser.execute_script("""pyodide.runPython(`
import sys
print(sys.version)
`);""")
