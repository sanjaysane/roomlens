"""Locale parity: identical keys, identical placeholder sets, valid UTF-8."""

from __future__ import annotations

import json
import re
from pathlib import Path

LOCALES = Path(__file__).resolve().parents[1] / "locales"
LANGS = ["en", "es", "hi"]


def load():
    return {
        lang: json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
        for lang in LANGS
    }


def placeholders(s: str) -> set:
    return set(re.findall(r"\{([a-z_]+)\}", s))


def test_key_parity():
    data = load()
    assert set(data["en"]) == set(data["es"]) == set(data["hi"])


def test_no_empty_strings():
    data = load()
    for lang, strings in data.items():
        for key, val in strings.items():
            assert val.strip(), f"{lang}.{key} is empty"


def test_placeholder_parity():
    data = load()
    for key in data["en"]:
        expect = placeholders(data["en"][key])
        for lang in LANGS[1:]:
            got = placeholders(data[lang][key])
            assert got == expect, f"{key}: en={expect} {lang}={got}"


def test_all_reply_keys_exist():
    """Every key referenced by ctx.reply(...) exists in en.json."""
    data = load()["en"]
    src = (LOCALES.parent / "src").rglob("*.py")
    used = set()
    for f in src:
        for m in re.finditer(r'(?:ctx\.reply|i18n\.t)\(\s*"([a-z_]+)"',
                             f.read_text()):
            used.add(m.group(1))
    missing = used - set(data)
    assert not missing, missing
