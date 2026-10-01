import pandas as pd


def calculate_risk_assessment(domain_scores, risk_register):
    """
    Calculate residual risk and Expected Annual Loss (EAL)
    using the supplied risk register.

    Required risk-register columns:
    Risk
    Domain
    BaselineProbability
    FinancialImpactAED
    """

    results = []

    # Convert domain scores into a simple lookup dictionary.
    domain_score_map = {}

    for _, row in domain_scores.iterrows():
        domain_score_map[str(row["Domain"])] = float(row["DomainScore"])

    for _, risk in risk_register.iterrows():

        domain = str(risk["Domain"])

        # If the domain is not found, use 0 rather than crashing.
        maturity_score = domain_score_map.get(domain, 0.0)

        baseline_probability = float(
            risk["BaselineProbability"]
        )

        financial_impact = float(
            risk["FinancialImpactAED"]
        )

        # Higher maturity reduces residual probability.
        maturity_factor = max(
            0.0,
            min(1.0, maturity_score / 100.0)
        )

        residual_probability = (
            baseline_probability * (1 - maturity_factor)
        )

        expected_annual_loss = (
            residual_probability * financial_impact
        )

        if residual_probability >= 0.30:
            risk_level = "High"
        elif residual_probability >= 0.10:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        results.append({
            "Risk": risk["Risk"],
            "Domain": domain,
            "BaselineProbability": baseline_probability,
            "FinancialImpactAED": financial_impact,
            "MaturityScore": maturity_score,
            "ResidualProbability": residual_probability,
            "ResidualRiskScore": residual_probability * 100,
            "ExpectedAnnualLossAED": expected_annual_loss,
            "RiskLevel": risk_level,
        })

    return pd.DataFrame(results)