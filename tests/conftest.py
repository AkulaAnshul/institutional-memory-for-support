"""Shared test fixtures and a fake Groq client.

The fake client lets us exercise the full tool-calling loop and the retry logic
without network access or an API key.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.fake_memory import FakeMemory
from app.models import Customer


# ---------------------------------------------------------------------------
# Fake Groq client
# ---------------------------------------------------------------------------
class _Function:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, call_id: str, name: str, arguments: dict) -> None:
        self.id = call_id
        self.function = _Function(name, json.dumps(arguments))


class _Message:
    def __init__(self, content: str | None = None, tool_calls=None) -> None:
        self.content = content
        self.tool_calls = tool_calls


class _Response:
    def __init__(self, message: _Message) -> None:
        self.choices = [SimpleNamespace(message=message)]


class _Completions:
    def __init__(self, script):
        self.script = list(script)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return _Response(step)


class FakeGroq:
    def __init__(self, script):
        self.completions = _Completions(script)
        self.chat = SimpleNamespace(completions=self.completions)


def tool_call_message(*calls) -> _Message:
    return _Message(tool_calls=[_ToolCall(f"call{i}", name, args) for i, (name, args) in enumerate(calls)])


def text_message(text: str) -> _Message:
    return _Message(content=text)


class ApiError(Exception):
    def __init__(self, status_code: int, message: str | None = None, headers: dict | None = None) -> None:
        super().__init__(message or f"HTTP {status_code}")
        self.status_code = status_code
        self.response = SimpleNamespace(status_code=status_code, headers=headers or {})


@pytest.fixture
def customer() -> Customer:
    return Customer(
        id="c01",
        name="Priya Nair",
        company="Northwind Analytics",
        plan="Enterprise",
        region="India",
        environment="Snowflake warehouse, 240 seats, SSO via Okta",
        csm="Ravi K.",
    )


@pytest.fixture
def memory() -> FakeMemory:
    return FakeMemory()
