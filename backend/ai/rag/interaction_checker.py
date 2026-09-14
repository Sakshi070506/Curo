"""
Module   : Drug Interaction Checker
Owner    : ML Engineer
Purpose  : Flags potential drug-drug interactions from extracted meds.
"""

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DrugInteraction:
    drug_a: str
    drug_b: str
    severity: str
    mechanism: str
    reference: str


class InteractionChecker:
    """Checks for drug-drug interactions from a reference dataset."""

    def __init__(self, csv_path: str | None = None):
        if csv_path:
            self.csv_path = csv_path
        elif os.getenv("DRUG_INTERACTIONS_CSV"):
            self.csv_path = os.getenv("DRUG_INTERACTIONS_CSV")
        else:
            # Default to backend/data/drug_interactions.csv
            self.csv_path = str(Path(__file__).parent.parent.parent / "data" / "drug_interactions.csv")
        self._interactions: list[DrugInteraction] = []
        self._load_interactions()

    def _load_interactions(self):
        """Load interactions from CSV file."""
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._interactions.append(DrugInteraction(
                        drug_a=row["drug_a"].lower().strip(),
                        drug_b=row["drug_b"].lower().strip(),
                        severity=row["severity"].lower().strip(),
                        mechanism=row["mechanism"].strip(),
                        reference=row["reference"].strip(),
                    ))
        except FileNotFoundError:
            pass

    def check(self, medications: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Check a list of medications for pairwise interactions.

        Args:
            medications: List of medication dicts with 'name' key

        Returns:
            List of interaction dicts with drug_a, drug_b, severity, mechanism, reference
        """
        drug_names = [med.get("name", "").lower().strip() for med in medications if med.get("name")]
        drug_names = [d for d in drug_names if d]

        results = []
        for i, drug_a in enumerate(drug_names):
            for drug_b in drug_names[i+1:]:
                interaction = self._find_interaction(drug_a, drug_b)
                if interaction:
                    results.append({
                        "drug_a": drug_a.title(),
                        "drug_b": drug_b.title(),
                        "severity": interaction.severity,
                        "mechanism": interaction.mechanism,
                        "reference": interaction.reference,
                    })

        return results

    def _find_interaction(self, drug_a: str, drug_b: str) -> DrugInteraction | None:
        """Find interaction between two drugs (order-independent)."""
        for interaction in self._interactions:
            if ((interaction.drug_a == drug_a and interaction.drug_b == drug_b) or
                (interaction.drug_a == drug_b and interaction.drug_b == drug_a)):
                return interaction
        return None

    def check_single(self, drug_a: str, drug_b: str) -> DrugInteraction | None:
        """Check interaction between two specific drugs."""
        return self._find_interaction(drug_a.lower().strip(), drug_b.lower().strip())

    def get_severity_priority(self, severity: str) -> int:
        """Get numeric priority for sorting (higher = more severe)."""
        priorities = {"critical": 4, "high": 3, "moderate": 2, "low": 1}
        return priorities.get(severity.lower(), 0)

    def get_highest_severity(self, interactions: list[dict[str, Any]]) -> str:
        """Get the highest severity from a list of interactions."""
        if not interactions:
            return "none"
        return max(interactions, key=lambda x: self.get_severity_priority(x["severity"]))["severity"]


def check_interactions(medications: list[dict[str, Any]], csv_path: str | None = None) -> list[dict[str, Any]]:
    """Convenience function to check interactions."""
    checker = InteractionChecker(csv_path)
    return checker.check(medications)


__all__ = [
    "DrugInteraction",
    "InteractionChecker",
    "check_interactions",
]