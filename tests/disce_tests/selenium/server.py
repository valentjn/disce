#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socket import socket
from threading import Thread

import disce
import pytest


def _get_http_request_handler_type(server_root_dir: Path) -> type[SimpleHTTPRequestHandler]:
    class HTTPRequestHandler(SimpleHTTPRequestHandler):
        def __init__(
            self, request: socket | tuple[bytes, socket], client_address: tuple[str, int], server: HTTPServer
        ) -> None:
            super().__init__(request, client_address, server, directory=str(server_root_dir))

    return HTTPRequestHandler


@pytest.fixture(scope="session")
def server_root_dir() -> Path:
    return Path(disce.__file__).parent.parent.parent


@pytest.fixture(scope="session")
def server_url(server_root_dir: Path) -> Generator[str]:
    host = "127.0.0.1"
    server = HTTPServer((host, 0), _get_http_request_handler_type(server_root_dir))
    url = f"http://{host}:{server.server_port}/"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield url
    server.shutdown()
    server.server_close()
    thread.join()
