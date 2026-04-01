"""Shared SSL context helpers for outbound HTTPS requests."""

from __future__ import annotations

import glob
import os
import ssl
from pathlib import Path


def _certifi_ca_bundle() -> str | None:
    """Return certifi's CA bundle path when available.

    We prefer certifi because it gives us a consistent trust store across
    platforms, but the rest of the app must still work when that dependency has
    not been installed into the active virtualenv yet.
    """

    try:
        import certifi
    except ImportError:
        return None
    return str(certifi.where())


def _python_org_ca_bundle_candidates() -> list[str]:
    """Return python.org macOS certificate bundle candidates.

    The macOS ``Install Certificates.command`` script shipped by python.org
    installs links under the framework's ``etc/openssl/cert.pem`` location, so
    we derive that path from any matching app bundle and also include any
    already-present framework cert files directly.
    """

    candidates: list[str] = []

    for install_script in sorted(glob.glob("/Applications/Python*/Install Certificates.command")):
        app_name = Path(install_script).parent.name
        version = app_name.removeprefix("Python").strip()
        if version:
            candidates.append(
                f"/Library/Frameworks/Python.framework/Versions/{version}/etc/openssl/cert.pem"
            )

    candidates.extend(
        sorted(glob.glob("/Library/Frameworks/Python.framework/Versions/*/etc/openssl/cert.pem"))
    )
    return candidates


def _ca_bundle_candidates() -> list[str]:
    """Return the CA bundle search order for outbound HTTPS verification."""

    candidates: list[str] = []
    certifi_bundle = _certifi_ca_bundle()
    if certifi_bundle:
        candidates.append(certifi_bundle)

    candidates.append("/etc/ssl/cert.pem")
    candidates.extend(_python_org_ca_bundle_candidates())
    candidates.append("/usr/local/etc/openssl/cert.pem")

    unique_candidates: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)
    return unique_candidates


def _resolve_ca_bundle() -> str | None:
    """Return the first existing CA bundle path from the fallback chain."""

    for candidate in _ca_bundle_candidates():
        if os.path.isfile(candidate):
            return candidate
    return None


def get_ssl_context() -> ssl.SSLContext:
    """Return a verified SSL context that still works on macOS Python installs.

    Some macOS Python distributions start with an empty default trust store, so
    callers need one shared place that keeps verification enabled while loading
    the best available CA bundle from known locations.
    """

    context = ssl.create_default_context()
    ca_bundle = _resolve_ca_bundle()
    if ca_bundle:
        context.load_verify_locations(cafile=ca_bundle)
    return context
