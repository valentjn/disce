# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from disce.tts import Voice, get_available_voices, speak


class TestVoice:
    @staticmethod
    def test_str() -> None:
        voice = Voice(name="test_name", language="test_language")
        assert str(voice) == "test_language: test_name"


def test_get_available_voices() -> None:
    voices = get_available_voices()
    assert isinstance(voices, list)
    for voice in voices:
        assert isinstance(voice, Voice)


def test_speak() -> None:
    speak("test_text", None, volume=0.0)
