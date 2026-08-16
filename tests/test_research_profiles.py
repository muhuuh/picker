from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import replace
import json
import unittest

from stock_research.research_profiles import (
    assert_write_allowed,
    build_research_run_spec,
    get_research_profile,
    list_research_profiles,
    write_research_run_spec,
)


class ResearchProfileTests(unittest.TestCase):
    def test_required_profiles_have_distinct_output_contracts(self):
        profiles = {profile.profile_id: profile for profile in list_research_profiles()}

        self.assertEqual(
            set(profiles),
            {"portfolio_update", "company_deep_research", "industry_deep_research", "candidate_discovery"},
        )
        self.assertEqual(len({profile.output_contract for profile in profiles.values()}), 4)
        self.assertEqual(profiles["portfolio_update"].depth, "delta_first_materiality_triggered")
        self.assertEqual(profiles["company_deep_research"].subject_types, ("company",))

    def test_on_demand_profiles_cannot_mutate_portfolio_or_strategy(self):
        for profile_id in ("company_deep_research", "industry_deep_research", "candidate_discovery"):
            profile = get_research_profile(profile_id)
            self.assertFalse(profile.write_permissions.portfolio_membership)
            self.assertFalse(profile.write_permissions.strategy)
            with self.assertRaises(PermissionError):
                assert_write_allowed(profile, "portfolio_membership")

    def test_run_spec_validates_subject_type_and_serializes_profile_snapshot(self):
        spec = build_research_run_spec(
            "company_deep_research",
            run_id="2026-08-16_company-deep-hir-0001",
            request_id="HIR-0001",
            request="Research ACME",
            subjects=({"subject_type": "company", "subject_id": "ACME"},),
        )

        with TemporaryDirectory() as temp_dir:
            path = write_research_run_spec(Path(temp_dir), spec)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["profile"]["profile_id"], "company_deep_research")
        self.assertFalse(payload["profile"]["write_permissions"]["portfolio_membership"])
        self.assertEqual(payload["subjects"][0]["subject_id"], "ACME")

        with self.assertRaisesRegex(ValueError, "does not support subject type"):
            build_research_run_spec(
                "company_deep_research",
                run_id="invalid",
                request_id="HIR-0002",
                request="Research an industry",
                subjects=({"subject_type": "industry", "subject_id": "chips"},),
            )

    def test_run_spec_writer_enforces_profile_permission(self):
        spec = build_research_run_spec(
            "company_deep_research",
            run_id="denied",
            request_id="HIR-0003",
            request="Research ACME",
            subjects=({"subject_type": "company", "subject_id": "ACME"},),
        )
        denied_permissions = replace(spec.profile.write_permissions, run_artifacts=False)
        denied_spec = replace(spec, profile=replace(spec.profile, write_permissions=denied_permissions))

        with TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(PermissionError, "run_artifacts"):
                write_research_run_spec(Path(temp_dir), denied_spec)

            self.assertFalse((Path(temp_dir) / "agents" / "runs" / "denied").exists())


if __name__ == "__main__":
    unittest.main()
