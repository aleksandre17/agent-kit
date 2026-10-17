"""Unit: the secrets policy's settings-file gates refuse a committed credential in the names settings
files give one, and admit the names that are not one (secrets 1.4.2, found by a second audit)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

GATES = {g["id"]: g for g in json.loads((Path(__file__).resolve().parents[2] / "policies" / "secrets" / "payload"
                                         / "edit-gates.json").read_text(encoding="utf-8"))["gates"]}
JSON_GATE, PROPERTIES_GATE = GATES["no-committed-config-secret"], GATES["no-committed-config-secret-in-properties"]


@pytest.mark.parametrize("line, refused", [
    ('"Key": "0123456789abcdef0123456789abcdef"', True), ('"Key": "__JWT_KEY__"', False),
    ('"API_KEY": "abcdefgh12345"', True), ('"api_key": "abcdefgh12345"', True), ('"apikey": "abcdefgh12345"', True),
    ('"JWT_SECRET": "abcdefgh12345"', True), ('"Pwd": "abcdefgh12345"', True), ('"ClientSecret": "abcdefghijk"', True),
    ('"DB_PASSWORD": "__DB_PASSWORD__"', False), ('"Key": "${JWT_KEY}"', False), ('"Password": ""', False),
    ('"key": "ConnectionStrings:DefaultConnection"', False), ('"ApiKeyHeaderName": "X-Api-Key-Header"', False),
    ('"ASPNETCORE_ENVIRONMENT": "Development"', False), ('"PublicKeyToken": "b77a5c561934e089"', False),
])
def test_a_settings_secret_is_refused_by_any_name_it_is_given(line, refused):
    assert bool(re.search(JSON_GATE["forbids"], line)) is refused


def test_launch_settings_are_settings_and_a_catalogue_is_not():
    paths = re.compile(JSON_GATE["paths"])
    assert paths.search("src/Api/Properties/launchSettings.json") and paths.search("api/appsettings.Production.json")
    assert not paths.search("ops/config/schema/config-keys.json") and not paths.search("package.json")


@pytest.mark.parametrize("line, refused", [
    ("    password: Sup3rS3cretValue", True), ("jwt.secret=abcdefgh12345", True), ("  client-secret: 'abcdefgh12345'", True),
    ("    password: ${DB_PASSWORD}", False), ("api-key: __API_KEY__", False), ("token-expiry: 3600000", False),
    ("spring.datasource.username: inout_app", False),
])
def test_a_properties_secret_is_refused_and_a_reference_admitted(line, refused):
    assert bool(re.search(PROPERTIES_GATE["forbids"], line, re.M)) is refused
    assert re.search(PROPERTIES_GATE["paths"], "src/main/resources/application-prod.yml")
