import pandas as pd

def calculate_domain_scores(responses, questionnaire):
    merged = responses.merge(
        questionnaire[["QuestionID", "Domain", "MaxScore"]],
        on="QuestionID",
        how="left"
    )
    scores = (
        merged.groupby("Domain")
        .agg(
            TotalResponse=("Response", "sum"),
            MaximumScore=("MaxScore", "sum"),
            QuestionCount=("QuestionID", "count")
        )
        .reset_index()
    )
    scores["DomainScore"] = (
        scores["TotalResponse"] / scores["MaximumScore"] * 100
    ).round(2)
    return scores

def calculate_overall_score(domain_scores, domain_weights):
    return round(
        sum(
            row["DomainScore"] * domain_weights.get(row["Domain"], 0)
            for _, row in domain_scores.iterrows()
        ),
        2
    )

def classify_maturity(score, maturity_levels):
    for level in maturity_levels:
        if level["min"] <= score <= level["max"]:
            return level["level"]
    return "Unknown"

def generate_recommendations(domain_scores):
    out = []
    for _, row in domain_scores.iterrows():
        s = row["DomainScore"]
        domain = row["Domain"]
        priority = (
            "Critical" if s < 40
            else "High" if s < 60
            else "Medium" if s < 80
            else "Monitor"
        )
        if priority != "Monitor":
            out.append({
                "Domain": domain,
                "Score": s,
                "Priority": priority,
                "Recommendation": f"Prioritise improvement activities for {domain} security."
            })
    return out
