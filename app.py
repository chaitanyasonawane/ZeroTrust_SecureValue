import json
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
from models.maturity_engine import calculate_domain_scores,calculate_overall_score,classify_maturity,generate_recommendations
from models.risk_engine import calculate_risk_assessment
from models.financial_engine import calculate_financial_evaluation

BASE=Path(__file__).parent
CONFIG=json.loads((BASE/"config.json").read_text())
Q=pd.read_csv(BASE/"data/questionnaire.csv")
RISK=pd.read_csv(BASE/"data/risk_register.csv")
st.set_page_config(page_title="Zero Trust Business Value Assessment",page_icon="🛡️",layout="wide")
st.title("🛡️ Zero Trust Business Value Assessment")
st.caption("Step 3B — Maturity + Cyber Risk + Financial Evaluation")

if "result" not in st.session_state: st.session_state.result=None

with st.form("assessment"):
    st.subheader("1. Organisation Details")
    a,b,c,d=st.columns(4)
    org=a.text_input("Organisation Name")
    industry=b.selectbox("Industry",["Finance","Healthcare","Technology","Government","Education","Energy","Retail","Other"])
    employees=c.number_input("Number of Employees",1,10000000,100)
    country=d.text_input("Country","UAE")
    st.divider()
    st.subheader("2. Zero Trust Maturity Assessment")
    labels={1:"1 — Not Implemented",2:"2 — Planned",3:"3 — Partially Implemented",4:"4 — Mostly Implemented",5:"5 — Fully Implemented"}
    answers=[]
    for domain,g in Q.groupby("Domain",sort=False):
        st.markdown(f"### {domain}")
        for _,q in g.iterrows():
            v=st.radio(q["Question"],[1,2,3,4,5],format_func=lambda x:labels[x],horizontal=True,key=f"q_{q['QuestionID']}")
            answers.append({"QuestionID":q["QuestionID"],"Response":v})
    st.divider()
    st.subheader("3. Financial Scenario Inputs")
    st.info("These are explicit user/research inputs. The application does not silently add investment or operating costs.")
    x,y,z,w=st.columns(4)
    investment=x.number_input("Initial Investment (AED)",min_value=0.0,value=0.0,step=1000.0)
    operating=y.number_input("Annual Operating Cost (AED)",min_value=0.0,value=0.0,step=1000.0)
    years=z.number_input("Analysis Period (Years)",1,30,int(CONFIG["financial_ui_defaults"]["analysis_years"]))
    discount=w.number_input("Discount Rate (%)",0.0,100.0,float(CONFIG["financial_ui_defaults"]["discount_rate"]),step=.5)
    st.caption("Annual financial benefit is derived from the risk model as baseline EAL minus residual EAL.")
    submit=st.form_submit_button("Calculate Maturity, Risk & Financial Value",type="primary",use_container_width=True)

if submit:
    if not org.strip() or not country.strip(): st.error("Organisation name and country are required."); st.stop()
    ds=calculate_domain_scores(pd.DataFrame(answers),Q)
    overall=calculate_overall_score(ds,CONFIG["domain_weights"])
    level=classify_maturity(overall,CONFIG["maturity_levels"])
    risks=calculate_risk_assessment(ds,RISK)
    baseline=float((RISK["BaselineProbability"]*RISK["FinancialImpactAED"]).sum())
    residual=float(risks["ExpectedAnnualLossAED"].sum())
    benefit=max(0.0,baseline-residual)
    fin=calculate_financial_evaluation(investment,operating,benefit,int(years),discount/100)
    st.session_state.result={"org":org,"ds":ds,"overall":overall,"level":level,"risks":risks,"baseline":baseline,"residual":residual,"benefit":benefit,"fin":fin,"rec":pd.DataFrame(generate_recommendations(ds))}

r=st.session_state.result
if r:
    st.divider(); st.header("4. Assessment Results")
    a,b,c,d=st.columns(4)
    a.metric("Maturity Score",f"{r['overall']:.2f}/100"); b.metric("Maturity Level",r["level"])
    c.metric("Baseline EAL",f"AED {r['baseline']:,.0f}"); d.metric("Residual EAL",f"AED {r['residual']:,.0f}")
    st.subheader("Zero Trust Domain Performance")
    st.dataframe(r["ds"][["Domain","DomainScore","QuestionCount"]].rename(columns={"DomainScore":"Score (%)","QuestionCount":"Questions"}),use_container_width=True,hide_index=True)
    st.plotly_chart(px.bar(r["ds"],x="Domain",y="DomainScore",range_y=[0,100],title="Zero Trust Maturity by Domain"),use_container_width=True)
    st.subheader("Cyber Risk Assessment")
    a,b,c=st.columns(3); a.metric("Annual Risk Reduction",f"AED {r['benefit']:,.0f}"); b.metric("High Risk Areas",int((r["risks"]["RiskLevel"]=="High").sum())); c.metric("Average Residual Risk",f"{r['risks']['ResidualRiskScore'].mean():.2f}")
    st.dataframe(r["risks"][["Risk","Domain","RiskLevel","ResidualRiskScore","ExpectedAnnualLossAED"]].rename(columns={"RiskLevel":"Level","ResidualRiskScore":"Risk Score","ExpectedAnnualLossAED":"Residual EAL (AED)"}),use_container_width=True,hide_index=True)
    st.divider(); st.subheader("5. Financial Evaluation")
    f=r["fin"]; a,b,c,d=st.columns(4)
    a.metric("Annual Benefit",f"AED {f['AnnualBenefitAED']:,.0f}"); b.metric("Net Annual Benefit",f"AED {f['NetAnnualBenefitAED']:,.0f}")
    c.metric("ROI",f"{f['ROI_Percent']:.2f}%" if f["ROI_Percent"] is not None else "N/A"); d.metric("Payback",f"{f['PaybackPeriodYears']:.2f} years" if f["PaybackPeriodYears"] is not None else "N/A")
    a,b=st.columns(2); a.metric("NPV",f"AED {f['NPV_AED']:,.0f}"); b.metric("IRR",f"{f['IRR_Percent']:.2f}%" if f["IRR_Percent"] is not None else "N/A")
    st.caption("Financial outputs are scenario results based on the explicit inputs above. They are not empirical findings.")
    st.dataframe(f["YearlyProjection"],use_container_width=True,hide_index=True)
    st.plotly_chart(px.line(f["YearlyProjection"],x="Year",y="CumulativeNetCashFlowAED",markers=True,title="Cumulative Net Cash Flow"),use_container_width=True)
    if not r["rec"].empty: st.subheader("Priority Recommendations"); st.dataframe(r["rec"],use_container_width=True,hide_index=True)

st.divider(); st.caption("Research prototype: risk and financial parameters must be sourced/justified and sensitivity-tested before dissertation findings are reported.")
