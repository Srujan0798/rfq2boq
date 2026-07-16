"""Unit tests for SectionClassifier."""

from src.preproc.sections import (
    PageSectionType,
    SectionClassifier,
    _get_markers,
)


class TestSectionClassifierInit:
    def test_classifier_initializes(self):
        clf = SectionClassifier()
        assert clf is not None

    def test_markers_loaded(self):
        markers = _get_markers()
        assert isinstance(markers, dict)
        assert "BOQ" in markers
        assert "FRONT_MATTER" in markers


class TestClassifyPage:
    def setup_method(self):
        self.clf = SectionClassifier()

    def test_empty_text_returns_unknown(self):
        result = self.clf.classify_page("", 0)
        assert result == PageSectionType.UNKNOWN

    def test_whitespace_only_returns_unknown(self):
        result = self.clf.classify_page("   \n\t  ", 0)
        assert result == PageSectionType.UNKNOWN

    def test_strong_boq_header_returns_boq(self):
        text = "BILL OF QUANTITIES\n1.1 Supply of cement 100 kg"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.BOQ

    def test_strong_boq_header_lowercase_returns_boq(self):
        text = "bill of quantities\n1.1 supply of cement 100 kg"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.BOQ

    def test_boq_abbreviation_returns_boq(self):
        text = "BOQ Schedule\nItem descriptions follow"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.BOQ

    def test_schedule_of_quantities_returns_boq(self):
        text = "SCHEDULE OF QUANTITIES\n1.1 Item description 50 m3"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.BOQ

    def test_abstract_of_quantities_returns_boq(self):
        text = "Abstract of Quantities\nItem 1: 100 kg cement"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.BOQ

    def test_strong_front_matter_header_returns_front_matter(self):
        text = "NOTICE INVITING TENDER\nEligibility criteria follow"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.FRONT_MATTER

    def test_nit_returns_front_matter(self):
        text = "NIT - Notice Inviting Tender\nScope of work as per CPWD"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.FRONT_MATTER

    def test_instruction_to_bidders_returns_front_matter(self):
        text = "INSTRUCTIONS TO BIDDERS\n1. Bid submission guidelines"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.FRONT_MATTER

    def test_emd_returns_front_matter(self):
        text = "EMD Details\nEarnest Money Deposit via RTGS"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.FRONT_MATTER

    def test_table_heuristic_3_rows_returns_boq(self):
        lines = [
            "1.1  Supply and laying of PCC  100  cum",
            "1.2  Reinforcement steel  500  kg",
            "1.3  Formwork  200  sqm",
        ]
        text = "\n".join(lines)
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.BOQ

    def test_table_heuristic_2_rows_returns_unknown(self):
        lines = [
            "1.1  Supply and laying of PCC  100  cum",
            "1.2  Reinforcement steel  500  kg",
        ]
        text = "\n".join(lines)
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.UNKNOWN

    def test_technical_spec_returns_tech_spec(self):
        text = "TECHNICAL SPECIFICATIONS\nConcrete grade M20 as per IS 456"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.TECHNICAL_SPEC

    def test_general_conditions_returns_general(self):
        text = "GENERAL CONDITIONS OF CONTRACT\nTerms and conditions apply"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.GENERAL_CONDITIONS

    def test_annexure_returns_annexure(self):
        text = "ANNEXURE A\nStandard forms for bid submission"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.ANNEXURE

    def test_random_text_returns_unknown(self):
        text = "Lorem ipsum dolor sit amet consectetur adipiscing elit"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.UNKNOWN

    def test_schedule_alone_ambiguous_returns_front_matter(self):
        text = "SCHEDULE A - ELIGIBILITY CRITERIA\nQualification requirements"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.FRONT_MATTER

    def test_validity_of_tender_returns_commercial(self):
        text = "Validity of Tender: 180 days\nFor all engaged manpower"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.COMMERCIAL

    def test_safety_goggles_returns_commercial(self):
        text = "Safety Goggles and Helmets shall be provided"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.COMMERCIAL

    def test_ppe_returns_commercial(self):
        text = "PPE requirements for all site personnel"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.COMMERCIAL

    def test_insurance_returns_commercial(self):
        text = "Insurance coverage during construction period"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.COMMERCIAL

    def test_penalty_clause_returns_commercial(self):
        text = "Liquidated damages and penalty for delay"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.COMMERCIAL

    def test_boq_still_beats_commercial(self):
        text = "BILL OF QUANTITIES\nValidity of Tender: 180 days"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.BOQ

    def test_bank_guarantee_returns_commercial(self):
        text = "Bank Guarantee details for performance security"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.COMMERCIAL

    def test_liquidated_damages_returns_commercial(self):
        text = "Liquidated Damages as per contract conditions"
        result = self.clf.classify_page(text, 0)
        assert result == PageSectionType.COMMERCIAL


class TestFindBoqPages:
    def setup_method(self):
        self.clf = SectionClassifier()

    def test_empty_pages_returns_empty(self):
        result = self.clf.find_boq_pages([])
        assert result == []

    def test_single_boq_page(self):
        pages = ["", "BILL OF QUANTITIES\n1.1 Item 100 kg"]
        result = self.clf.find_boq_pages(pages)
        assert result == [1]

    def test_returns_contiguous_range(self):
        pages = [
            "NOTICE INVITING TENDER",
            "INSTRUCTIONS TO BIDDERS",
            "BILL OF QUANTITIES",
            "SCHEDULE OF QUANTITIES",
            "Item 1: 100 kg",
            "Item 2: 50 m3",
            "TECHNICAL SPECIFICATIONS",
        ]
        result = self.clf.find_boq_pages(pages)
        assert len(result) > 0
        assert result == list(range(result[0], result[-1] + 1))

    def test_no_boq_pages_falls_back_to_all(self):
        pages = [
            "NOTICE INVITING TENDER",
            "ELIGIBILITY CRITERIA",
            "INSTRUCTIONS TO BIDDERS",
        ]
        result = self.clf.find_boq_pages(pages)
        assert result == [0, 1, 2]

    def test_secondary_heuristic_detects_boq_with_quantity_unit_pairs(self):
        # Test the secondary heuristic: >=3 quantity-unit pairs within 1000 chars -> BOQ
        pages = [
            "NOTICE INVITING TENDER",
            "1. Cement 100 kg\n2. Sand 50 kg\n3. Aggregate 30 kg",  # Should be detected as BOQ
            "OTHER CONTENT HERE",
        ]
        result = self.clf.find_boq_pages(pages)
        assert result == [1]  # Only the middle page should be detected

    def test_secondary_heuristic_ignores_pages_with_fewer_than_3_pairs(self):
        # Should not trigger with fewer than 3 pairs
        pages = [
            "NOTICE INVITING TENDER",
            "1. Cement 100 kg\n2. Sand 50 kg",  # Only 2 pairs -> should not be BOQ
            "OTHER CONTENT HERE",
        ]
        result = self.clf.find_boq_pages(pages)
        # Should fall back to all pages since no BOQ detected via primary or secondary heuristic
        assert result == [0, 1, 2]

    def test_secondary_heuristic_works_with_different_units(self):
        pages = [
            "HEADER",
            "Item A 10 sqm\nItem B 20 cum\nItem C 30 kg\nItem D 40 nos",  # 4 pairs
            "FOOTER",
        ]
        result = self.clf.find_boq_pages(pages)
        assert result == [1]  # Middle page detected

    def test_secondary_heuristic_full_text_for_pdf_improvement(self):
        # Updated for S4_IMPROVE_PDF_EXTRACTION: we intentionally use full page text (removed 1000 char limit)
        # so that BOQ signals (qty-unit pairs) anywhere in a real PDF page are detected.
        # This improves section detection for long/weak PDFs (e.g. 01 GSECL) where relevant text may not be in first 1000 chars.
        # Justification: 1000-char window was too limiting per real tender analysis in resources/ and S4 diagnosis.
        long_prefix = "A" * 1100
        suffix = "1. Cement 100 kg\n2. Sand 50 kg\n3. Aggregate 30 kg"
        pages = [
            "HEADER",
            long_prefix + suffix,  # Pairs now detected (full text)
            "FOOTER",
        ]
        result = self.clf.find_boq_pages(pages)
        # With full-text C2 (S4), the middle page triggers, so exact candidates include it (not full fallback)
        assert 1 in result
        assert len(result) <= len(pages)  # focused, not necessarily all

    def test_secondary_heuristic_ignores_non_quantity_numbers(self):
        # Numbers that aren't quantities (like years, item numbers) shouldn't count without units nearby
        pages = [
            "HEADER",
            "Year 2023\nItem 1. Description\nItem 2. Another",  # No units near numbers
            "FOOTER",
        ]
        result = self.clf.find_boq_pages(pages)
        assert result == [0, 1, 2]  # Falls back to all

    def test_secondary_heuristic_ignores_spec_pages_with_density(self):
        # Spec pages might have density values like kg/m3 but shouldn't trigger BOQ
        pages = [
            "HEADER",
            "Density: 2500 kg/m3\nSpecific gravity: 2.5\nWater absorption: 2%",  # No proper quantity-unit pairs
            "FOOTER",
        ]
        result = self.clf.find_boq_pages(pages)
        assert result == [0, 1, 2]  # Falls back to all


class TestBackwardCompat:
    def test_classify_section_still_exists(self):
        from src.preproc.sections import classify_section

        result = classify_section("Test Section", "Some content")
        assert result is not None

    def test_extract_sections_still_exists(self):
        from src.preproc.sections import extract_sections

        result = extract_sections("1.1 Test heading\nSome content")
        assert isinstance(result, list)
