from datetime import date
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from stock_research.evidence import (
    Claim,
    EvidencePacket,
    Source,
    default_packet_path,
    new_packet,
    read_packet,
    validate_packet,
    write_packet,
)


class EvidenceTests(unittest.TestCase):
    def test_new_packet_builds_stable_id(self):
        packet = new_packet(
            provider="Exa API",
            subject_type="industry",
            subject_id="European Defense",
            current_date=date(2026, 5, 3),
        )

        self.assertEqual(packet.packet_id, "2026-05-03_exa_api_industry_european_defense")
        self.assertEqual(packet.provider, "Exa API")

    def test_validate_packet_checks_source_references(self):
        packet = EvidencePacket(
            packet_id="test",
            created_at="2026-05-03T00:00:00",
            provider="provider_test",
            subject_type="company",
            subject_id="ASML",
            time_window="latest",
            sources=[
                Source(
                    source_id="src1",
                    provider="provider_test",
                    source_type="web",
                    title="Example",
                    url="https://example.com",
                )
            ],
            claims=[Claim(claim="ASML has news.", evidence="Example evidence.", source_ids=["src1"], confidence="medium")],
        )

        report = validate_packet(packet)

        self.assertTrue(report.ok, report.errors)

    def test_validate_packet_rejects_unknown_source_reference(self):
        packet = EvidencePacket(
            packet_id="test",
            created_at="2026-05-03T00:00:00",
            provider="provider_test",
            subject_type="company",
            subject_id="ASML",
            time_window="latest",
            claims=[Claim(claim="ASML has news.", evidence="Example evidence.", source_ids=["missing"])],
        )

        report = validate_packet(packet)

        self.assertFalse(report.ok)
        self.assertIn("references unknown source_id 'missing'", "\n".join(report.errors))

    def test_write_and_read_packet_round_trips(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet = new_packet("provider_test", "provider_test", "smoke", current_date=date(2026, 5, 3))
            path = default_packet_path(root, "2026-05-09_weekly", packet)

            write_packet(packet, path)
            loaded = read_packet(path)

            self.assertEqual(loaded.packet_id, packet.packet_id)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
