"""Rental property cash-flow math. No UI here, so it is easy to test.

All money is in dollars. Percent inputs are plain numbers (7 means 7%).
"""
from dataclasses import dataclass, field, fields


@dataclass
class Inputs:
    # --- Purchase & loan ---
    purchase_price: float = 200_000
    down_payment_pct: float = 20        # % of price
    closing_costs: float = 6_000        # $ paid at closing (usually 2-5% of price)
    rehab_costs: float = 0              # $ repairs needed before renting
    interest_rate: float = 7.0          # % per year
    loan_term_years: float = 30
    pmi_rate: float = 0.5               # % of loan per year, only if down < 20%

    # --- Income (monthly) ---
    monthly_rent: float = 2_000
    other_income: float = 0             # parking, laundry, pet fees...
    vacancy_pct: float = 5              # % of rent lost to empty months

    # --- Fixed expenses ---
    # Each amount has a matching "_period": "year" or "month".
    property_tax: float = 2_400
    property_tax_period: str = "year"
    insurance: float = 1_200
    insurance_period: str = "year"
    hoa: float = 0
    hoa_period: str = "month"
    utilities: float = 0                # utilities the owner pays
    utilities_period: str = "month"
    other_costs: float = 0              # lawn, pest control, snow...
    other_costs_period: str = "month"

    # --- Percent-of-rent expenses ---
    maintenance_pct: float = 5          # small repairs, % of gross rent
    capex_pct: float = 5                # big-ticket savings (roof, HVAC), % of gross rent
    management_pct: float = 8           # property manager, % of collected rent


@dataclass
class Results:
    loan_amount: float = 0
    down_payment: float = 0
    cash_invested: float = 0
    mortgage_pi: float = 0              # monthly principal + interest
    pmi_monthly: float = 0
    gross_income: float = 0             # monthly rent + other income
    vacancy_loss: float = 0
    effective_income: float = 0         # income after vacancy
    operating_expenses: float = 0       # monthly, excludes mortgage
    total_expenses: float = 0           # monthly, operating + mortgage + PMI
    noi_yearly: float = 0
    cash_flow_monthly: float = 0
    cash_flow_yearly: float = 0
    cap_rate: float = 0                 # %
    cash_on_cash: float = 0             # %
    dscr: float = 0                     # NOI / yearly debt payments
    rent_to_price: float = 0            # % (1% rule)
    expense_ratio: float = 0            # % of gross income (50% rule)
    breakdown: dict = field(default_factory=dict)   # monthly expense lines
    verdict: str = ""
    reasons: list = field(default_factory=list)     # (passed: bool|None, text)


PERIODS = ("year", "month")


def to_monthly(amount: float, period: str) -> float:
    """Turn an amount entered per year or per month into a monthly amount."""
    if period == "year":
        return amount / 12
    if period == "month":
        return amount
    raise ValueError(f"period must be 'year' or 'month', got {period!r}")


def monthly_payment(loan: float, annual_rate_pct: float, years: float) -> float:
    """Standard mortgage formula: P * r / (1 - (1 + r)^-n)."""
    n = int(round(years * 12))
    if loan <= 0 or n <= 0:
        return 0.0
    r = annual_rate_pct / 100 / 12
    if r == 0:
        return loan / n
    return loan * r / (1 - (1 + r) ** -n)


def analyze(i: Inputs) -> Results:
    res = Results()

    # Purchase & loan
    res.down_payment = i.purchase_price * i.down_payment_pct / 100
    res.loan_amount = max(i.purchase_price - res.down_payment, 0)
    res.cash_invested = res.down_payment + i.closing_costs + i.rehab_costs
    res.mortgage_pi = monthly_payment(res.loan_amount, i.interest_rate, i.loan_term_years)
    res.pmi_monthly = (res.loan_amount * i.pmi_rate / 100 / 12
                       if i.down_payment_pct < 20 else 0.0)

    # Income
    res.gross_income = i.monthly_rent + i.other_income
    res.vacancy_loss = res.gross_income * i.vacancy_pct / 100
    res.effective_income = res.gross_income - res.vacancy_loss

    # Operating expenses (monthly, no mortgage)
    b = {
        "Property tax": to_monthly(i.property_tax, i.property_tax_period),
        "Insurance": to_monthly(i.insurance, i.insurance_period),
        "HOA": to_monthly(i.hoa, i.hoa_period),
        "Utilities": to_monthly(i.utilities, i.utilities_period),
        "Other": to_monthly(i.other_costs, i.other_costs_period),
        "Maintenance": i.monthly_rent * i.maintenance_pct / 100,
        "CapEx": i.monthly_rent * i.capex_pct / 100,
        "Management": res.effective_income * i.management_pct / 100,
    }
    res.operating_expenses = sum(b.values())
    b["Mortgage (P&I)"] = res.mortgage_pi
    b["PMI"] = res.pmi_monthly
    res.breakdown = b
    res.total_expenses = res.operating_expenses + res.mortgage_pi + res.pmi_monthly

    # Results
    res.noi_yearly = (res.effective_income - res.operating_expenses) * 12
    res.cash_flow_monthly = res.effective_income - res.total_expenses
    res.cash_flow_yearly = res.cash_flow_monthly * 12
    res.cap_rate = res.noi_yearly / i.purchase_price * 100 if i.purchase_price else 0
    res.cash_on_cash = (res.cash_flow_yearly / res.cash_invested * 100
                        if res.cash_invested else 0)
    debt_yearly = (res.mortgage_pi + res.pmi_monthly) * 12
    res.dscr = res.noi_yearly / debt_yearly if debt_yearly else float("inf")
    res.rent_to_price = i.monthly_rent / i.purchase_price * 100 if i.purchase_price else 0
    res.expense_ratio = (res.operating_expenses / res.gross_income * 100
                         if res.gross_income else 0)

    _verdict(res)
    return res


def _verdict(res: Results) -> None:
    """Score the deal on four simple checks and pick Good / OK / Poor.

    Benchmarks (common investor rules of thumb, not laws):
      - Monthly cash flow: $200+ good, $0+ OK
      - Cash-on-cash return: 8%+ good, 4%+ OK
      - DSCR (can rent cover the loan?): 1.25+ good, 1.0+ OK
      - 1% rule: monthly rent >= 1% of price
    """
    cf, coc, dscr = res.cash_flow_monthly, res.cash_on_cash, res.dscr
    reasons = []

    if cf >= 200:
        reasons.append((True, f"Strong cash flow: ${cf:,.0f}/month left over."))
    elif cf >= 0:
        reasons.append((None, f"Thin cash flow: only ${cf:,.0f}/month left over (aim for $200+)."))
    else:
        reasons.append((False, f"Loses money: ${-cf:,.0f}/month out of your pocket."))

    if coc >= 8:
        reasons.append((True, f"Cash-on-cash return {coc:.1f}% beats the 8% target."))
    elif coc >= 4:
        reasons.append((None, f"Cash-on-cash return {coc:.1f}% is modest (target 8%+)."))
    else:
        reasons.append((False, f"Cash-on-cash return {coc:.1f}% is weak (target 8%+)."))

    if dscr >= 1.25:
        reasons.append((True, f"Rent covers the loan comfortably (DSCR {dscr:.2f})."))
    elif dscr >= 1.0:
        reasons.append((None, f"Rent barely covers the loan (DSCR {dscr:.2f}, lenders like 1.25+)."))
    else:
        reasons.append((False, f"Rent doesn't cover the loan (DSCR {dscr:.2f})."))

    if res.rent_to_price >= 1:
        reasons.append((True, f"Passes the 1% rule (rent is {res.rent_to_price:.2f}% of price)."))
    else:
        reasons.append((False, f"Fails the 1% rule (rent is {res.rent_to_price:.2f}% of price)."))

    good = sum(1 for ok, _ in reasons if ok is True)
    bad = sum(1 for ok, _ in reasons if ok is False)

    if cf < 0 or dscr < 1.0:
        res.verdict = "Poor"
    elif good >= 3 and bad == 0:
        res.verdict = "Good"
    elif bad >= 2:
        res.verdict = "Poor"
    else:
        res.verdict = "OK"
    res.reasons = reasons


def input_names():
    return [f.name for f in fields(Inputs) if not f.name.endswith("_period")]
