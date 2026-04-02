import pytest

from apps.approvals.services import required_approval_types_for_risk
from apps.core.choices import ApprovalType


@pytest.mark.parametrize(
    ("risk_tier", "expected"),
    [
        ("low", [ApprovalType.TECHNICAL]),
        ("medium", [ApprovalType.TECHNICAL, ApprovalType.PRODUCT]),
        ("high", [ApprovalType.TECHNICAL, ApprovalType.PRODUCT, ApprovalType.RISK]),
        (
            "critical",
            [
                ApprovalType.TECHNICAL,
                ApprovalType.PRODUCT,
                ApprovalType.RISK,
                ApprovalType.GOVERNANCE,
            ],
        ),
    ],
)
def test_required_approval_types_for_risk_returns_expected_policy(risk_tier, expected):
    assert required_approval_types_for_risk(risk_tier) == expected
