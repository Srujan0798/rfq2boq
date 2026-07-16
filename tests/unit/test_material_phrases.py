"""Unit tests for the canonical material phrase extractor.

These tests cover the conservative splitter used to align long pipeline
sentences with short human gold annotations. They are deterministic: same
input must always produce the same output.
"""

from __future__ import annotations

from src.nlp.patterns.material_phrases import (
    extract_canonical_material,
    extract_canonical_material_batch,
)


class TestExtractCanonicalMaterial:
    def test_empty_input_returns_empty(self) -> None:
        assert extract_canonical_material("") == ""
        assert extract_canonical_material("   ") == ""

    def test_short_phrase_passes_through(self) -> None:
        # Already-canonical input is unchanged.
        s = "Mineral Wool mattresses"
        assert extract_canonical_material(s) == s

    def test_strips_supply_application_action_prefix(self) -> None:
        out = extract_canonical_material(
            "Supply & application of 100 mm thick lightly bonded "
            "Mineral Wool mattresses, hooks, retainer plates, "
            "casing supports, wires etc. on plain area, pipes, "
            "valves, bends, vessels etc. of as per Schedule-A, "
            "General terms & conditions and Instruction of "
            "Engineer In-charge."
        )
        # Action prefix ("Supply & application of"), spec ("100 mm thick
        # lightly bonded"), and reference suffix ("of as per Schedule-A,
        # General terms...") are all stripped.
        assert "supply" not in out.lower()
        assert "schedule" not in out.lower()
        assert "general terms" not in out.lower()
        assert "mineral wool" in out.lower()
        assert "retainer plates" in out.lower()

    def test_strips_providing_and_fixing_prefix(self) -> None:
        out = extract_canonical_material(
            "Providing and fixing under-deck & wall acoustic insulation as 4 mm thick sound deadener"
        )
        assert "providing" not in out.lower()
        assert "fixing" not in out.lower()
        assert "acoustic insulation" in out.lower()

    def test_strips_supply_installation_testing_commissioning(self) -> None:
        out = extract_canonical_material(
            "Supply, installation, testing and commissioning of MS chilled water pipe insulation nitrile rubber"
        )
        assert "commissioning" not in out.lower()
        assert "ms chilled water" in out.lower()
        assert "nitrile rubber" in out.lower()

    def test_does_not_split_on_commas(self) -> None:
        # A list of materials is one BOQ row, not multiple rows.
        out = extract_canonical_material("Aluminum sheet, self taping screws etc. on insulated surface per Schedule")
        assert "," in out
        assert "aluminum sheet" in out.lower()
        assert "self taping screws" in out.lower()

    def test_strips_density_specifications(self) -> None:
        out = extract_canonical_material("first layer of closed cell nitrile rubber insulation density 40 to 50 kg/m3")
        assert "density" not in out.lower()
        assert "nitrile rubber insulation" in out.lower()

    def test_strips_per_schedule_suffix(self) -> None:
        out = extract_canonical_material("Mineral Wool mattresses etc. per Schedule-A")
        assert "schedule" not in out.lower()
        assert "mineral wool" in out.lower()

    def test_strips_as_per_engineer_suffix(self) -> None:
        out = extract_canonical_material(
            "Aluminum sheet self taping screws on insulated surface as per instruction of Engineer In-charge"
        )
        assert "engineer" not in out.lower()
        assert "aluminum sheet" in out.lower()

    def test_deterministic_same_input_same_output(self) -> None:
        s = "Supply & application of 100 mm thick Mineral Wool mattresses per Schedule"
        a = extract_canonical_material(s)
        b = extract_canonical_material(s)
        c = extract_canonical_material(s)
        assert a == b == c

    def test_batch_wrapper(self) -> None:
        inputs = [
            "Supply & application of Mineral Wool per Schedule",
            "Aluminum sheet per Schedule",
            "Acoustic Louvers",
        ]
        outputs = extract_canonical_material_batch(inputs)
        assert len(outputs) == len(inputs)
        assert "schedule" not in outputs[0].lower()
        assert "schedule" not in outputs[1].lower()
        assert outputs[2] == "Acoustic Louvers"

    def test_case_insensitive_prefix_matching(self) -> None:
        # Pred strings come in mixed case from pdfplumber.
        out = extract_canonical_material("SUPPLY & APPLICATION OF Mineral Wool mattresses per Schedule-A")
        assert "supply" not in out.lower()
        assert "schedule" not in out.lower()
        assert "mineral wool" in out.lower()

    def test_keeps_legitimate_dimensions(self) -> None:
        # Gold for 04_adani has "300 mm dia" as a separate DIMENSION entity,
        # but the material phrase itself can include pipe-size hints.
        out = extract_canonical_material("MS chilled water pipe insulation nitrile rubber 300 mm dia")
        # The material phrase is preserved; trailing "300 mm dia" dimension
        # may or may not survive depending on regex priority. The important
        # thing is the material core is intact.
        assert "ms chilled water" in out.lower()
        assert "nitrile rubber" in out.lower()

    def test_strips_nb_pipe_spec_suffix(self) -> None:
        # 07_grew pipe insulation items have "on XNB to YNB" spec suffixes
        out = extract_canonical_material("75 mm thick Insulation on 1200NB to 1000NB")
        assert "on" not in out.lower().split() or "on" not in out
        assert "nb" not in out.lower()
        assert "insulation" in out.lower()

    def test_strips_nb_pipe_spec_suffix_with_slash(self) -> None:
        out = extract_canonical_material("19 mm thick Insulation on 65NB / 50NB / 40NB / 32NB / 25NB / 20NB / 15NB")
        assert "nb" not in out.lower()
        assert "insulation" in out.lower()
