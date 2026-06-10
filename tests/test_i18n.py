from whatsapp_export_viewer.i18n import load_translations, normalize_language
from whatsapp_export_viewer.gui import ViewerApp


def test_normalizes_supported_languages():
    assert normalize_language("pt_BR") == "pt-BR"
    assert normalize_language("es-MX") == "es"
    assert normalize_language("fr-FR") == "en"


def test_translations_have_expected_keys():
    for language in ("en", "pt-BR", "es"):
        translations = load_translations(language)
        assert translations["app_title"] == "WhatsApp Export Viewer"
        assert translations["generate"]


def test_gui_class_is_importable():
    assert ViewerApp is not None
