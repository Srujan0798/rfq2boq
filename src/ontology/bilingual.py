"""Bilingual ontology: English + Hindi material/unit translations."""

MATERIAL_TRANSLATIONS = {
    "cement": ["सीमेंट", "cement"],
    "steel": ["स्टील", "इस्पात"],
    "brick": ["ईंट", "brick"],
    "concrete": ["कंक्रीट", "concrete"],
    "sand": ["रेत", "sand"],
    "aggregate": ["aggregate", "जोड़"],
    "glass": ["कांच", "glass"],
    "tile": ["tile", "टाइल"],
    "waterproofing": ["waterproofing", "जलरोधक"],
    "plaster": ["plaster", "प्लास्टर"],
    "flooring": ["flooring", "फर्श"],
    "door": ["door", "दरवाजा"],
    "window": ["window", "खिड़की"],
    "paint": ["paint", "पेंट"],
    "pipe": ["pipe", "पाइप"],
}

UNIT_TRANSLATIONS = {
    "cum": ["cum", "घन मीटर", "क्यूम"],
    "sqm": ["sqm", "वर्ग मीटर", "एसक्यूएम"],
    "kg": ["kg", "किलोग्राम"],
    "nos": ["nos", "संख्या", "नंबर"],
    "m": ["m", "मीटर"],
    "ltr": ["ltr", "लीटर"],
}

LOCATION_TRANSLATIONS = {
    "ground floor": ["ground floor", "भूतल", "ग्राउंड फ्लोर"],
    "first floor": ["first floor", "पहली मंजिल"],
    "second floor": ["second floor", "दूसरी मंजिल"],
    "basement": ["basement", "बेसमेंट"],
    "roof": ["roof", "छत"],
    "foundation": ["foundation", "नींव"],
}


class BilingualOntology:
    def lookup(self, term: str, lang: str = "en") -> dict | None:
        """Look up a term in either language."""
        term_lower = term.lower()

        for category, translations in [
            ("material", MATERIAL_TRANSLATIONS),
            ("unit", UNIT_TRANSLATIONS),
            ("location", LOCATION_TRANSLATIONS),
        ]:
            for canonical, variants in translations.items():
                if term_lower in variants:
                    return {"canonical": canonical, "category": category, "language": lang}

        return None

    def get_hindi_name(self, english_term: str) -> str | None:
        mat = MATERIAL_TRANSLATIONS.get(english_term.lower())
        if mat:
            return mat[0]
        return None
