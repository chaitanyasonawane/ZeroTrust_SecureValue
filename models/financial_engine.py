import pandas as pd

def _npv(rate, flows):
    return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(flows))

def _irr(flows):
    lo, hi = -0.999, 10.0
    flo, fhi = _npv(lo, flows), _npv(hi, flows)
    for _ in range(30):
        if flo * fhi <= 0: break
        hi *= 2; fhi = _npv(hi, flows)
    if flo * fhi > 0: return None
    for _ in range(200):
        mid=(lo+hi)/2; fm=_npv(mid, flows)
        if abs(fm)<1e-9: return mid
        if flo*fm<=0: hi=mid
        else: lo=mid; flo=fm
    return (lo+hi)/2

def calculate_financial_evaluation(initial_investment, annual_operating_cost,
                                   annual_benefit, analysis_years, discount_rate):
    initial_investment=float(initial_investment)
    annual_operating_cost=float(annual_operating_cost)
    annual_benefit=float(annual_benefit)
    years=int(analysis_years)
    rate=float(discount_rate)
    if min(initial_investment, annual_operating_cost, annual_benefit) < 0:
        raise ValueError("Financial amounts cannot be negative.")
    if years < 1: raise ValueError("Analysis period must be at least 1 year.")
    if rate <= -1: raise ValueError("Discount rate must be greater than -100%.")

    net=annual_benefit-annual_operating_cost
    total_benefit=annual_benefit*years
    total_cost=initial_investment+annual_operating_cost*years
    total_net=total_benefit-total_cost
    roi=((total_benefit-total_cost)/total_cost*100) if total_cost else None
    payback=(initial_investment/net) if net>0 and initial_investment>0 else (0.0 if initial_investment==0 else None)
    flows=[-initial_investment]+[net]*years
    npv=_npv(rate,flows); irr=_irr(flows)
    rows=[]; cumulative=-initial_investment
    for y in range(1,years+1):
        cumulative+=net
        rows.append({"Year":y,"AnnualBenefitAED":round(annual_benefit,2),
                     "OperatingCostAED":round(annual_operating_cost,2),
                     "NetAnnualBenefitAED":round(net,2),
                     "CumulativeNetCashFlowAED":round(cumulative,2)})
    return {"InitialInvestmentAED":initial_investment,"AnnualOperatingCostAED":annual_operating_cost,
            "AnnualBenefitAED":annual_benefit,"AnalysisYears":years,"DiscountRate":rate,
            "NetAnnualBenefitAED":round(net,2),"TotalBenefitsAED":round(total_benefit,2),
            "TotalCostAED":round(total_cost,2),"TotalNetBenefitAED":round(total_net,2),
            "ROI_Percent":round(roi,2) if roi is not None else None,
            "PaybackPeriodYears":round(payback,2) if payback is not None else None,
            "NPV_AED":round(npv,2),"IRR_Percent":round(irr*100,2) if irr is not None else None,
            "YearlyProjection":pd.DataFrame(rows)}
