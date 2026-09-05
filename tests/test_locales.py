"""Locale parity: identical keys, identical placeholder sets, valid UTF-8."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.i18n import I18n

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


# ── Marathi (mr): declared partial locale with English fallback ──────────
# Policy (see BRIEF.md): en/es/hi keep strict key parity; mr covers the
# customer/prospect-facing demo keys, and I18n.t falls back to English for
# every key mr does not define. This is deliberate, not a parity hole.

def test_mr_is_subset_of_en():
    i18n = I18n(str(LOCALES))
    assert set(i18n.keys("mr")) <= set(i18n.keys("en")), "mr must not invent keys"


def test_mr_no_empty_strings():
    i18n = I18n(str(LOCALES))
    for key in i18n.keys("mr"):
        assert i18n.t("mr", key).strip(), f"mr.{key} is empty"


def test_mr_placeholder_parity_for_defined_keys():
    import re
    i18n = I18n(str(LOCALES))
    en = {k: i18n.t("en", k) for k in i18n.keys("en")}
    for key in i18n.keys("mr"):
        got = set(re.findall(r"\{([a-z_]+)\}", i18n.t("mr", key)))
        want = set(re.findall(r"\{([a-z_]+)\}", en[key]))
        assert got == want, f"mr.{key}: placeholders {got} != en {want}"


def test_mr_falls_back_to_english_for_missing_keys():
    i18n = I18n(str(LOCALES))
    en_keys = set(i18n.keys("en"))
    mr_keys = set(i18n.keys("mr"))
    missing = sorted(en_keys - mr_keys)
    assert missing, "expected mr to be partial (some keys missing)"
    for key in missing[:25]:
        assert i18n.t("mr", key) == i18n.t("en", key), f"no fallback for {key}"


def test_language_menu_lists_four_languages():
    i18n = I18n(str(LOCALES))
    for lang in ("en", "es", "hi", "mr"):
        menu = i18n.t(lang, "language_menu")
        assert "4" in menu and "मराठी" in menu, f"{lang} menu missing Marathi"


def test_prospect_marathi_from_welcome_sticks_for_viz(tmp_path):
    """Picking Marathi before registration must persist: the visualization
    caption the designer later triggers is pushed in Marathi."""
    from conftest import DESIGNER, PROSPECT, Chat, make_image, make_noisy_image

    chat = Chat(tmp_path)
    # designer onboards (English) and adds a product
    chat.send(DESIGNER, "hi")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "Casa Studio")
    chat.send(DESIGNER, "1")  # catalog
    chat.send(DESIGNER, "1")  # add product
    chat.send(DESIGNER, "Aria Chair")
    chat.send(DESIGNER, "189.00")
    chat.send(DESIGNER, "1")  # floor item
    chat.media.register("cutout1",
                        make_image(size=(300, 400), color=(200, 60, 40)))
    chat.send(DESIGNER, None, msg_type="image", media_id="cutout1")
    chat.send(DESIGNER, "0")

    # prospect picks Marathi FIRST — no prospect row exists yet
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "language")
    chat.send(PROSPECT, "4")
    assert chat.db.get_prospect(PROSPECT) is None or \
        chat.db.get_prospect(PROSPECT)["preferred_language"] == "mr"
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "1")
    assert chat.db.get_prospect(PROSPECT)["preferred_language"] == "mr"
    chat.media.register("room1", make_noisy_image())
    chat.send(PROSPECT, None, msg_type="image", media_id="room1")
    chat.send(PROSPECT, "1")  # opt-in

    # designer renders and sends the visualization
    chat.send(DESIGNER, "2")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "3")

    captions = chat.image_captions(PROSPECT)
    assert captions, "prospect got no visualization"
    assert any("तुमच्याच खोलीत" in c for c in captions), captions
