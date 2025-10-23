#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from collections.abc import Generator

import pytest
from disce.pyscript import (
    Element,
    Event,
    EventBinding,
    alert,
    append_child,
    confirm,
    create_element,
    download_file,
    hide_element,
    is_null,
    prompt,
    set_theme,
    show_element,
    upload_file,
)
from pyodide.ffi import JsNull
from pyscript import document, window

from disce_tests.injected.tools import print_signal

_logger = logging.getLogger(__name__)


class TestEventBinding:
    @staticmethod
    def test_register_unregister() -> None:
        clicked = False

        def on_click(event: Event) -> None:
            nonlocal clicked
            clicked = True

        element = create_element("div")
        binding = EventBinding(element, "click", on_click)
        binding.register()
        element.dispatchEvent(window.Event.new("click"))
        assert clicked
        clicked = False
        binding.unregister()
        element.dispatchEvent(window.Event.new("click"))
        assert not clicked


class TestCreateElement:
    @staticmethod
    def test_tag() -> None:
        element = create_element("div")
        assert element.tagName == "DIV"

    @staticmethod
    def test_children() -> None:
        child1 = create_element("span")
        child2 = create_element("p")
        parent = create_element("div", child1, child2)
        assert parent.childNodes.length == 2
        assert parent.childNodes[0].isSameNode(child1)
        assert parent.childNodes[1].isSameNode(child2)

    @staticmethod
    def test_text() -> None:
        element = create_element("div", text="test")
        assert element.innerText == "test"

    @staticmethod
    def test_html() -> None:
        element = create_element("div", html="<span>inner</span>")
        assert element.innerHTML == "<span>inner</span>"

    @staticmethod
    def test_event_listeners() -> None:
        triggered = {"click": False, "mouseover": False}

        def on_click(event: Event) -> None:
            triggered["click"] = True

        def on_mouseover(event: Event) -> None:
            triggered["mouseover"] = True

        element = create_element(
            "div",
            event_listeners={
                "click": on_click,
                "mouseover": on_mouseover,
            },
        )
        element.dispatchEvent(window.Event.new("click"))
        assert triggered["click"]
        element.dispatchEvent(window.Event.new("mouseover"))
        assert triggered["mouseover"]

    @staticmethod
    def test_attributes() -> None:
        element = create_element("div", id_="test_id", data_value="test_value")
        assert element.getAttribute("id") == "test_id"
        assert element.getAttribute("data-value") == "test_value"


def test_append_child() -> None:
    parent = create_element("div")
    child = append_child(parent, "span", text="child")
    assert parent.childNodes.length == 1
    assert parent.childNodes[0].isSameNode(child)
    assert child.tagName == "SPAN"
    assert child.innerText == "child"


@pytest.fixture
def inserted_element() -> Generator[Element]:
    element = create_element("div")
    document.body.appendChild(element)
    yield element
    document.body.removeChild(element)


def test_hide_element(inserted_element: Element) -> None:
    style = window.getComputedStyle(inserted_element)
    hide_element(inserted_element)
    assert style.display == "none"
    hide_element(inserted_element, hide=False)
    assert style.display != "none"


def test_show_element(inserted_element: Element) -> None:
    style = window.getComputedStyle(inserted_element)
    show_element(inserted_element)
    assert style.display != "none"
    show_element(inserted_element, show=False)
    assert style.display == "none"


@pytest.fixture
def restore_theme() -> Generator[None]:
    original_theme = document.documentElement.getAttribute("data-bs-theme")
    yield
    if original_theme is None:
        document.documentElement.removeAttribute("data-bs-theme")
    else:
        document.documentElement.setAttribute("data-bs-theme", original_theme)


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_set_theme(theme: str, restore_theme: None) -> None:
    set_theme(theme)
    assert document.documentElement.getAttribute("data-bs-theme") == theme


def test_set_theme_auto(restore_theme: None) -> None:
    set_theme()
    assert document.documentElement.getAttribute("data-bs-theme") in {"dark", "light"}


def test_download_file() -> None:
    download_file("test_pyscript_test_download_file.json", "application/json", '{"key": "value"}')


def test_upload_file(capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest) -> None:
    def listener(content_: str) -> None:
        if content_ == '{"key": "value"}':
            print_signal("listener_called_correctly", capsys, request)

    element = upload_file("application/json", listener)
    data_transfer = window.DataTransfer.new()
    data_transfer.items.add(
        window.File.new(['{"key": "value"}'], "test_pyscript_test_upload_file.json", {"type": "application/json"})
    )
    element.files = data_transfer.files
    element.dispatchEvent(window.Event.new("change"))


def test_alert(capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest) -> None:
    print_signal("before_alert", capsys, request)
    alert("message")


def test_confirm_accepted(capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest) -> None:
    print_signal("before_confirm", capsys, request)
    assert confirm("message")


def test_confirm_dismissed(capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest) -> None:
    print_signal("before_confirm", capsys, request)
    assert not confirm("message")


def test_prompt_accepted(capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest) -> None:
    print_signal("before_prompt", capsys, request)
    assert prompt("message", "default_value") == "user_value"


def test_prompt_default(capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest) -> None:
    print_signal("before_prompt", capsys, request)
    assert prompt("message", "default_value") == "default_value"


def test_prompt_dismissed(capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest) -> None:
    print_signal("before_prompt", capsys, request)
    assert prompt("message", "default_value") is None


def test_is_null() -> None:
    assert is_null(JsNull())
    assert not is_null("non_null_value")
