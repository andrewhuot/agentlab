"""Tests for shared SSL context resolution across macOS-friendly CA bundles."""

from __future__ import annotations

import builtins
import sys
from types import SimpleNamespace

from shared.ssl_context import get_ssl_context


class _StubSSLContext:
    """Capture CA bundle loads performed by the shared SSL helper."""

    def __init__(self) -> None:
        self.loaded_cafiles: list[str] = []

    def load_verify_locations(self, cafile: str | None = None, **_: object) -> None:
        """Record the CA file chosen for verification."""
        if cafile is not None:
            self.loaded_cafiles.append(cafile)


def test_get_ssl_context_prefers_certifi_bundle_when_available(monkeypatch) -> None:
    """The helper should prefer certifi when it can resolve a real bundle path."""
    from shared import ssl_context

    context = _StubSSLContext()

    monkeypatch.setitem(sys.modules, "certifi", SimpleNamespace(where=lambda: "/tmp/certifi.pem"))
    monkeypatch.setattr(ssl_context.ssl, "create_default_context", lambda: context)
    monkeypatch.setattr(
        ssl_context.os.path,
        "isfile",
        lambda path: path == "/tmp/certifi.pem",
    )

    resolved = get_ssl_context()

    assert resolved is context
    assert context.loaded_cafiles == ["/tmp/certifi.pem"]


def test_get_ssl_context_falls_back_to_system_cert_file_without_certifi(monkeypatch) -> None:
    """The helper should use `/etc/ssl/cert.pem` when certifi cannot be imported."""
    from shared import ssl_context

    context = _StubSSLContext()
    original_import = builtins.__import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: ANN001
        if name == "certifi":
            raise ImportError("certifi unavailable")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    monkeypatch.setattr(ssl_context.ssl, "create_default_context", lambda: context)
    monkeypatch.setattr(
        ssl_context.os.path,
        "isfile",
        lambda path: path == "/etc/ssl/cert.pem",
    )

    resolved = get_ssl_context()

    assert resolved is context
    assert context.loaded_cafiles == ["/etc/ssl/cert.pem"]


def test_get_ssl_context_uses_python_org_framework_bundle_when_present(monkeypatch) -> None:
    """The helper should derive the framework cert path from python.org installers."""
    from shared import ssl_context

    context = _StubSSLContext()
    original_import = builtins.__import__
    expected_bundle = "/Library/Frameworks/Python.framework/Versions/3.12/etc/openssl/cert.pem"

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: ANN001
        if name == "certifi":
            raise ImportError("certifi unavailable")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    monkeypatch.setattr(ssl_context.ssl, "create_default_context", lambda: context)
    monkeypatch.setattr(
        ssl_context.glob,
        "glob",
        lambda pattern: ["/Applications/Python 3.12/Install Certificates.command"],
    )
    monkeypatch.setattr(
        ssl_context.os.path,
        "isfile",
        lambda path: path == expected_bundle,
    )

    resolved = get_ssl_context()

    assert resolved is context
    assert context.loaded_cafiles == [expected_bundle]


def test_get_ssl_context_uses_homebrew_bundle_as_last_resort(monkeypatch) -> None:
    """The helper should fall back to the Homebrew OpenSSL bundle last."""
    from shared import ssl_context

    context = _StubSSLContext()
    original_import = builtins.__import__
    expected_bundle = "/usr/local/etc/openssl/cert.pem"

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: ANN001
        if name == "certifi":
            raise ImportError("certifi unavailable")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    monkeypatch.setattr(ssl_context.ssl, "create_default_context", lambda: context)
    monkeypatch.setattr(ssl_context.glob, "glob", lambda pattern: [])
    monkeypatch.setattr(
        ssl_context.os.path,
        "isfile",
        lambda path: path == expected_bundle,
    )

    resolved = get_ssl_context()

    assert resolved is context
    assert context.loaded_cafiles == [expected_bundle]
