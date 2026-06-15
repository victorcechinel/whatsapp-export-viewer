from whatsapp_export_viewer.i18n import load_translations, normalize_language
from whatsapp_export_viewer.gui import ViewerApp


def test_normalizes_supported_languages():
    assert normalize_language("pt_BR") == "pt-BR"
    assert normalize_language("es-MX") == "es"
    assert normalize_language("fr-FR") == "en"


def test_translations_have_expected_keys():
    expected = set(load_translations("en"))
    for language in ("en", "pt-BR", "es"):
        translations = load_translations(language)
        assert set(translations) == expected
        assert translations["app_title"] == "WhatsApp Export Viewer"
        assert translations["generate"]
        assert translations["open_browser"]
        assert translations["viewer_chat"]


def test_gui_class_is_importable():
    assert ViewerApp is not None
