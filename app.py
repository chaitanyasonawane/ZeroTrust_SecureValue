import json
import io
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from models.maturity_engine import (
    calculate_domain_scores,
    calculate_overall_score,
    classify_maturity,
    generate_recommendations
)

from models.risk_engine import calculate_risk_assessment
from models.financial_engine import calculate_financial_evaluation


# ============================================================
# PATHS AND DATA
# ============================================================

BASE = Path(__file__).parent

CONFIG = json.loads(
    (BASE / "config.json").read_text()
)

Q = pd.read_csv(
    BASE / "data/questionnaire.csv"
)

RISK = pd.read_csv(
    BASE / "data/risk_register.csv"
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Zero Trust Business Value Assessment",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ Zero Trust Business Value Assessment")

st.caption(
    "TrustValue — Zero Trust Maturity, Cyber Risk and Financial Evaluation"
)


# ============================================================
# SESSION STATE
# ============================================================

if "result" not in st.session_state:
    st.session_state.result = None


# ============================================================
# PDF CHART GENERATION
# ============================================================

def create_pdf_charts(result):

    charts = {}

    # --------------------------------------------------------
    # 1. DOMAIN MATURITY BAR CHART
    # --------------------------------------------------------

    domain_data = result["ds"]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(
        domain_data["Domain"],
        domain_data["DomainScore"]
    )

    ax.set_title(
        "Zero Trust Maturity by Domain",
        fontsize=14,
        fontweight="bold"
    )

    ax.set_ylabel("Maturity Score (%)")
    ax.set_ylim(0, 100)

    plt.xticks(
        rotation=30,
        ha="right"
    )

    plt.tight_layout()

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=180,
        bbox_inches="tight"
    )

    plt.close(fig)

    buffer.seek(0)

    charts["domain"] = buffer


    # --------------------------------------------------------
    # 2. RISK COMPARISON CHART
    # --------------------------------------------------------

    fig, ax = plt.subplots(figsize=(7, 5))

    labels = [
        "Baseline EAL",
        "Residual EAL"
    ]

    values = [
        result["baseline"],
        result["residual"]
    ]

    ax.bar(
        labels,
        values
    )

    ax.set_title(
        "Baseline vs Residual Expected Annual Loss",
        fontsize=14,
        fontweight="bold"
    )

    ax.set_ylabel("AED")

    plt.tight_layout()

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=180,
        bbox_inches="tight"
    )

    plt.close(fig)

    buffer.seek(0)

    charts["risk"] = buffer


    # --------------------------------------------------------
    # 3. FINANCIAL METRICS CHART
    # --------------------------------------------------------

    financial = result["fin"]

    labels = []
    values = []

    if financial.get("ROI_Percent") is not None:
        labels.append("ROI (%)")
        values.append(
            financial["ROI_Percent"]
        )

    if financial.get("IRR_Percent") is not None:
        labels.append("IRR (%)")
        values.append(
            financial["IRR_Percent"]
        )

    if labels:

        fig, ax = plt.subplots(
            figsize=(7, 5)
        )

        ax.bar(
            labels,
            values
        )

        ax.set_title(
            "Financial Return Indicators",
            fontsize=14,
            fontweight="bold"
        )

        ax.set_ylabel("Percentage")

        plt.tight_layout()

        buffer = io.BytesIO()

        fig.savefig(
            buffer,
            format="png",
            dpi=180,
            bbox_inches="tight"
        )

        plt.close(fig)

        buffer.seek(0)

        charts["financial"] = buffer


    # --------------------------------------------------------
    # 4. DOMAIN PIE CHART
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(7, 7)
    )

    ax.pie(
        domain_data["DomainScore"],
        labels=domain_data["Domain"],
        autopct="%1.1f%%",
        startangle=90
    )

    ax.set_title(
        "Zero Trust Domain Score Distribution",
        fontsize=14,
        fontweight="bold"
    )

    plt.tight_layout()

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=180,
        bbox_inches="tight"
    )

    plt.close(fig)

    buffer.seek(0)

    charts["pie"] = buffer


    return charts


# ============================================================
# PDF REPORT GENERATION
# ============================================================

def generate_pdf_report(result):

    pdf_buffer = io.BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    story = []


    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "Zero Trust Business Value Assessment",
            styles["Title"]
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            "TrustValue — Assessment Report",
            styles["Heading2"]
        )
    )

    story.append(
        Spacer(1, 20)
    )


    # ========================================================
    # ORGANISATION INFORMATION
    # ========================================================

    story.append(
        Paragraph(
            "1. Organisation Information",
            styles["Heading2"]
        )
    )

    organisation_table = [
        ["Organisation", result["org"]],
        ["Industry", result["industry"]],
        ["Employees", str(result["employees"])],
        ["Country", result["country"]]
    ]

    table = Table(
        organisation_table,
        colWidths=[160, 300]
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 20)
    )


    # ========================================================
    # MATURITY RESULTS
    # ========================================================

    story.append(
        Paragraph(
            "2. Zero Trust Maturity Assessment",
            styles["Heading2"]
        )
    )

    maturity_table = [
        ["Measure", "Result"],
        [
            "Overall Maturity Score",
            f'{result["overall"]:.2f}/100'
        ],
        [
            "Maturity Level",
            result["level"]
        ]
    ]

    table = Table(
        maturity_table,
        colWidths=[250, 210]
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 15)
    )


    # ========================================================
    # DOMAIN SCORES
    # ========================================================

    story.append(
        Paragraph(
            "Domain-Level Maturity",
            styles["Heading3"]
        )
    )

    domain_table = [
        ["Domain", "Score (%)", "Questions"]
    ]

    for _, row in result["ds"].iterrows():

        domain_table.append([
            str(row["Domain"]),
            f'{row["DomainScore"]:.2f}',
            str(row["QuestionCount"])
        ])

    table = Table(
        domain_table,
        colWidths=[220, 100, 100]
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 20)
    )


    # ========================================================
    # RISK ASSESSMENT
    # ========================================================

    story.append(
        Paragraph(
            "3. Cybersecurity Risk Assessment",
            styles["Heading2"]
        )
    )

    risk_table = [
        ["Measure", "Value"],
        [
            "Baseline Expected Annual Loss",
            f'AED {result["baseline"]:,.2f}'
        ],
        [
            "Residual Expected Annual Loss",
            f'AED {result["residual"]:,.2f}'
        ],
        [
            "Modelled Annual Risk Reduction",
            f'AED {result["benefit"]:,.2f}'
        ]
    ]

    table = Table(
        risk_table,
        colWidths=[270, 190]
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 20)
    )


    # ========================================================
    # FINANCIAL RESULTS
    # ========================================================

    story.append(
        Paragraph(
            "4. Financial Evaluation",
            styles["Heading2"]
        )
    )

    financial = result["fin"]

    financial_table = [
        ["Metric", "Result"],
        [
            "Annual Benefit",
            f'AED {financial["AnnualBenefitAED"]:,.2f}'
        ],
        [
            "Net Annual Benefit",
            f'AED {financial["NetAnnualBenefitAED"]:,.2f}'
        ],
        [
            "ROI",
            (
                f'{financial["ROI_Percent"]:.2f}%'
                if financial["ROI_Percent"] is not None
                else "N/A"
            )
        ],
        [
            "NPV",
            f'AED {financial["NPV_AED"]:,.2f}'
        ],
        [
            "IRR",
            (
                f'{financial["IRR_Percent"]:.2f}%'
                if financial["IRR_Percent"] is not None
                else "N/A"
            )
        ],
        [
            "Payback Period",
            (
                f'{financial["PaybackPeriodYears"]:.2f} years'
                if financial["PaybackPeriodYears"] is not None
                else "N/A"
            )
        ]
    ]

    table = Table(
        financial_table,
        colWidths=[270, 190]
    )

    table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 20)
    )


    # ========================================================
    # CHARTS
    # ========================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "5. Visual Analysis",
            styles["Heading2"]
        )
    )

    charts = create_pdf_charts(result)


    story.append(
        Paragraph(
            "Zero Trust Domain Maturity",
            styles["Heading3"]
        )
    )

    story.append(
        Image(
            charts["domain"],
            width=6.5 * inch,
            height=3.5 * inch
        )
    )

    story.append(
        Spacer(1, 15)
    )


    story.append(
        Paragraph(
            "Baseline vs Residual Expected Annual Loss",
            styles["Heading3"]
        )
    )

    story.append(
        Image(
            charts["risk"],
            width=6.2 * inch,
            height=3.5 * inch
        )
    )


    story.append(
        PageBreak()
    )


    if "financial" in charts:

        story.append(
            Paragraph(
                "Financial Return Indicators",
                styles["Heading3"]
            )
        )

        story.append(
            Image(
                charts["financial"],
                width=6.2 * inch,
                height=3.5 * inch
            )
        )

        story.append(
            Spacer(1, 15)
        )


    story.append(
        Paragraph(
            "Zero Trust Domain Distribution",
            styles["Heading3"]
        )
    )

    story.append(
        Image(
            charts["pie"],
            width=5.8 * inch,
            height=5.0 * inch
        )
    )


    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "6. Priority Recommendations",
            styles["Heading2"]
        )
    )

    recommendations = result["rec"]

    if not recommendations.empty:

        for _, row in recommendations.iterrows():

            text = " | ".join(
                str(value)
                for value in row.values
                if str(value).strip()
            )

            story.append(
                Paragraph(
                    "• " + text,
                    styles["Normal"]
                )
            )

            story.append(
                Spacer(1, 8)
            )

    else:

        story.append(
            Paragraph(
                "No priority recommendations were generated.",
                styles["Normal"]
            )
        )


    # ========================================================
    # DISCLAIMER
    # ========================================================

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Note: The financial and risk outputs are modelled results "
            "based on the user-provided assessment inputs and assumptions. "
            "They should not be interpreted as verified organisational "
            "financial or cybersecurity outcomes.",
            styles["Normal"]
        )
    )


    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(story)

    pdf_buffer.seek(0)

    return pdf_buffer


# ============================================================
# INPUT FORM
# ============================================================

with st.form("assessment"):

    st.subheader("1. Organisation Details")

    a, b, c, d = st.columns(4)

    org = a.text_input(
        "Organisation Name"
    )

    industry = b.selectbox(
        "Industry",
        [
            "Finance",
            "Healthcare",
            "Technology",
            "Government",
            "Education",
            "Energy",
            "Retail",
            "Other"
        ]
    )

    employees = c.number_input(
        "Number of Employees",
        1,
        10000000,
        100
    )

    country = d.text_input(
        "Country",
        "UAE"
    )


    # ========================================================
    # MATURITY ASSESSMENT
    # ========================================================

    st.divider()

    st.subheader(
        "2. Zero Trust Maturity Assessment"
    )

    labels = {
        1: "1 — Not Implemented",
        2: "2 — Planned",
        3: "3 — Partially Implemented",
        4: "4 — Mostly Implemented",
        5: "5 — Fully Implemented"
    }

    answers = []

    for domain, g in Q.groupby(
        "Domain",
        sort=False
    ):

        st.markdown(
            f"### {domain}"
        )

        for _, q in g.iterrows():

            value = st.radio(
                q["Question"],
                [1, 2, 3, 4, 5],
                format_func=lambda x: labels[x],
                horizontal=True,
                key=f"q_{q['QuestionID']}"
            )

            answers.append({
                "QuestionID": q["QuestionID"],
                "Response": value
            })

        st.divider()


    # ========================================================
    # FINANCIAL INPUTS
    # ========================================================

    st.subheader(
        "3. Financial Scenario Inputs"
    )

    st.info(
        "These are explicit user/research inputs. "
        "The application does not silently add investment "
        "or operating costs."
    )

    x, y, z, w = st.columns(4)

    investment = x.number_input(
        "Initial Investment (AED)",
        min_value=0.0,
        value=0.0,
        step=1000.0
    )

    operating = y.number_input(
        "Annual Operating Cost (AED)",
        min_value=0.0,
        value=0.0,
        step=1000.0
    )

    years = z.number_input(
        "Analysis Period (Years)",
        1,
        30,
        int(
            CONFIG[
                "financial_ui_defaults"
            ]["analysis_years"]
        )
    )

    discount = w.number_input(
        "Discount Rate (%)",
        0.0,
        100.0,
        float(
            CONFIG[
                "financial_ui_defaults"
            ]["discount_rate"]
        ),
        step=0.5
    )

    st.caption(
        "Annual financial benefit is derived from "
        "baseline EAL minus residual EAL."
    )


    submit = st.form_submit_button(
        "Calculate Maturity, Risk & Financial Value",
        type="primary",
        use_container_width=True
    )


# ============================================================
# CALCULATIONS
# ============================================================

if submit:

    if not org.strip() or not country.strip():

        st.error(
            "Organisation name and country are required."
        )

        st.stop()


    # --------------------------------------------------------
    # MATURITY
    # --------------------------------------------------------

    ds = calculate_domain_scores(
        pd.DataFrame(answers),
        Q
    )

    overall = calculate_overall_score(
        ds,
        CONFIG["domain_weights"]
    )

    level = classify_maturity(
        overall,
        CONFIG["maturity_levels"]
    )


    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risks = calculate_risk_assessment(
        ds,
        RISK
    )

    baseline = float(
        (
            RISK["BaselineProbability"]
            *
            RISK["FinancialImpactAED"]
        ).sum()
    )

    residual = float(
        risks["ExpectedAnnualLossAED"].sum()
    )

    benefit = max(
        0.0,
        baseline - residual
    )


    # --------------------------------------------------------
    # FINANCIAL
    # --------------------------------------------------------

    fin = calculate_financial_evaluation(
        investment,
        operating,
        benefit,
        int(years),
        discount / 100
    )


    # --------------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------------

    recommendations = pd.DataFrame(
        generate_recommendations(ds)
    )


    # --------------------------------------------------------
    # STORE RESULTS
    # --------------------------------------------------------

    st.session_state.result = {

        "org": org,

        "industry": industry,

        "employees": employees,

        "country": country,

        "ds": ds,

        "overall": overall,

        "level": level,

        "risks": risks,

        "baseline": baseline,

        "residual": residual,

        "benefit": benefit,

        "fin": fin,

        "rec": recommendations
    }


# ============================================================
# RESULTS
# ============================================================

r = st.session_state.result


if r:

    st.divider()

    st.header(
        "4. Assessment Results"
    )


    # ========================================================
    # MAIN METRICS
    # ========================================================

    a, b, c, d = st.columns(4)

    a.metric(
        "Maturity Score",
        f'{r["overall"]:.2f}/100'
    )

    b.metric(
        "Maturity Level",
        r["level"]
    )

    c.metric(
        "Baseline EAL",
        f'AED {r["baseline"]:,.0f}'
    )

    d.metric(
        "Residual EAL",
        f'AED {r["residual"]:,.0f}'
    )


    # ========================================================
    # DOMAIN PERFORMANCE
    # ========================================================

    st.subheader(
        "Zero Trust Domain Performance"
    )

    st.dataframe(
        r["ds"][
            [
                "Domain",
                "DomainScore",
                "QuestionCount"
            ]
        ].rename(
            columns={
                "DomainScore": "Score (%)",
                "QuestionCount": "Questions"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


    # Existing bar chart

    st.plotly_chart(
        px.bar(
            r["ds"],
            x="Domain",
            y="DomainScore",
            range_y=[0, 100],
            title="Zero Trust Maturity by Domain"
        ),
        use_container_width=True
    )


    # ========================================================
    # NEW PIE CHART
    # ========================================================

    st.subheader(
        "Zero Trust Domain Distribution"
    )

    pie_col1, pie_col2 = st.columns(2)

    with pie_col1:

        pie_chart = px.pie(
            r["ds"],
            values="DomainScore",
            names="Domain",
            title="Domain Score Distribution"
        )

        st.plotly_chart(
            pie_chart,
            use_container_width=True
        )

    with pie_col2:

        st.info(
            "The pie chart provides a visual comparison "
            "of the contribution of each Zero Trust domain "
            "to the overall assessment."
        )


    # ========================================================
    # CYBER RISK
    # ========================================================

    st.subheader(
        "Cyber Risk Assessment"
    )

    a, b, c = st.columns(3)

    a.metric(
        "Annual Risk Reduction",
        f'AED {r["benefit"]:,.0f}'
    )

    b.metric(
        "High Risk Areas",
        int(
            (
                r["risks"]["RiskLevel"]
                == "High"
            ).sum()
        )
    )

    c.metric(
        "Average Residual Risk",
        f'{r["risks"]["ResidualRiskScore"].mean():.2f}'
    )


    st.dataframe(
        r["risks"][
            [
                "Risk",
                "Domain",
                "RiskLevel",
                "ResidualRiskScore",
                "ExpectedAnnualLossAED"
            ]
        ].rename(
            columns={
                "RiskLevel": "Level",
                "ResidualRiskScore": "Risk Score",
                "ExpectedAnnualLossAED": "Residual EAL (AED)"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # NEW RISK COMPARISON CHART
    # ========================================================

    risk_chart_data = pd.DataFrame({
        "Measure": [
            "Baseline EAL",
            "Residual EAL"
        ],
        "AED": [
            r["baseline"],
            r["residual"]
        ]
    })

    st.subheader(
        "Baseline vs Residual Risk"
    )

    st.plotly_chart(
        px.bar(
            risk_chart_data,
            x="Measure",
            y="AED",
            title="Expected Annual Loss Comparison",
            text_auto=".2f"
        ),
        use_container_width=True
    )


    # ========================================================
    # FINANCIAL EVALUATION
    # ========================================================

    st.divider()

    st.subheader(
        "5. Financial Evaluation"
    )

    f = r["fin"]

    a, b, c, d = st.columns(4)

    a.metric(
        "Annual Benefit",
        f'AED {f["AnnualBenefitAED"]:,.0f}'
    )

    b.metric(
        "Net Annual Benefit",
        f'AED {f["NetAnnualBenefitAED"]:,.0f}'
    )

    c.metric(
        "ROI",
        (
            f'{f["ROI_Percent"]:.2f}%'
            if f["ROI_Percent"] is not None
            else "N/A"
        )
    )

    d.metric(
        "Payback",
        (
            f'{f["PaybackPeriodYears"]:.2f} years'
            if f["PaybackPeriodYears"] is not None
            else "N/A"
        )
    )


    a, b = st.columns(2)

    a.metric(
        "NPV",
        f'AED {f["NPV_AED"]:,.0f}'
    )

    b.metric(
        "IRR",
        (
            f'{f["IRR_Percent"]:.2f}%'
            if f["IRR_Percent"] is not None
            else "N/A"
        )
    )


    st.caption(
        "Financial outputs are scenario results based "
        "on the explicit inputs above. They are not "
        "empirical findings."
    )


    # ========================================================
    # FINANCIAL TABLE
    # ========================================================

    st.dataframe(
        f["YearlyProjection"],
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # CASH FLOW CHART
    # ========================================================

    st.plotly_chart(
        px.line(
            f["YearlyProjection"],
            x="Year",
            y="CumulativeNetCashFlowAED",
            markers=True,
            title="Cumulative Net Cash Flow"
        ),
        use_container_width=True
    )


    # ========================================================
    # FINANCIAL METRICS CHART
    # ========================================================

    financial_chart_data = []

    if f["ROI_Percent"] is not None:

        financial_chart_data.append({
            "Metric": "ROI (%)",
            "Value": f["ROI_Percent"]
        })

    if f["IRR_Percent"] is not None:

        financial_chart_data.append({
            "Metric": "IRR (%)",
            "Value": f["IRR_Percent"]
        })


    if financial_chart_data:

        st.subheader(
            "Financial Return Indicators"
        )

        financial_df = pd.DataFrame(
            financial_chart_data
        )

        st.plotly_chart(
            px.bar(
                financial_df,
                x="Metric",
                y="Value",
                title="ROI and IRR"
            ),
            use_container_width=True
        )


    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    if not r["rec"].empty:

        st.subheader(
            "Priority Recommendations"
        )

        st.dataframe(
            r["rec"],
            use_container_width=True,
            hide_index=True
        )


    # ========================================================
    # DOWNLOAD PDF REPORT
    # ========================================================

    st.divider()

    st.subheader(
        "6. Final Assessment Report"
    )

    st.write(
        "Download the complete assessment including "
        "maturity results, risk analysis, financial results, "
        "charts and recommendations."
    )


    try:

        pdf = generate_pdf_report(r)

        st.download_button(
            label="📥 Download Complete PDF Report",
            data=pdf,
            file_name="TrustValue_Zero_Trust_Assessment_Report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    except Exception as e:

        st.error(
            f"Unable to generate PDF report: {e}"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Research prototype: risk and financial parameters "
    "must be sourced, justified and sensitivity-tested "
    "before being interpreted as organisational findings."
)