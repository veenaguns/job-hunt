"""Worked example, checked by hand. Run:  python -m unittest -v

Default inputs: $200,000 house, 20% down, 7% for 30 years, $2,000 rent.

  Down payment      = 200,000 x 20%                    = $40,000
  Loan              = 200,000 - 40,000                 = $160,000
  Cash invested     = 40,000 + 6,000 closing + 0 rehab = $46,000
  Mortgage (P&I)    = 160,000 x r / (1 - (1+r)^-360),
                      r = 0.07/12                      = $1,064.48 / mo
  Vacancy           = 2,000 x 5%                       = $100
  Collected rent    = 2,000 - 100                      = $1,900
  Operating costs   = tax 200 + insurance 100 + maintenance 100
                      + capex 100 + management (8% of 1,900) 152
                                                       = $652 / mo
  NOI               = (1,900 - 652) x 12               = $14,976 / yr
  Cash flow         = 1,900 - 652 - 1,064.48           = $183.52 / mo
                                                       = $2,202.24 / yr
  Cap rate          = 14,976 / 200,000                 = 7.488%
  Cash-on-cash      = 2,202.24 / 46,000                = 4.787%
  DSCR              = 14,976 / (1,064.48 x 12)         = 1.172
  1% rule           = 2,000 / 200,000                  = 1.00%  (pass)
  Verdict           = OK (positive but thin cash flow, modest CoC)
"""
import unittest

from calculator import Inputs, analyze, monthly_payment, to_monthly


class WorkedExample(unittest.TestCase):
    def setUp(self):
        self.r = analyze(Inputs())

    def test_mortgage(self):
        self.assertAlmostEqual(self.r.mortgage_pi, 1064.48, places=2)

    def test_core_numbers(self):
        r = self.r
        self.assertAlmostEqual(r.loan_amount, 160_000)
        self.assertAlmostEqual(r.cash_invested, 46_000)
        self.assertAlmostEqual(r.operating_expenses, 652.00, places=2)
        self.assertAlmostEqual(r.total_expenses, 1716.48, places=2)
        self.assertAlmostEqual(r.noi_yearly, 14_976.00, places=2)
        self.assertAlmostEqual(r.cash_flow_monthly, 183.52, places=2)
        self.assertAlmostEqual(r.cash_flow_yearly, 2202.24, places=1)

    def test_ratios(self):
        r = self.r
        self.assertAlmostEqual(r.cap_rate, 7.488, places=3)
        self.assertAlmostEqual(r.cash_on_cash, 4.787, places=3)
        self.assertAlmostEqual(r.dscr, 1.172, places=3)
        self.assertAlmostEqual(r.rent_to_price, 1.0)

    def test_verdict(self):
        self.assertEqual(self.r.verdict, "OK")

    def test_pmi_only_under_20_percent(self):
        self.assertEqual(self.r.pmi_monthly, 0)
        low = analyze(Inputs(down_payment_pct=10))
        self.assertAlmostEqual(low.pmi_monthly, 180_000 * 0.005 / 12)

    def test_bad_deal_is_poor(self):
        self.assertEqual(analyze(Inputs(monthly_rent=1200)).verdict, "Poor")

    def test_great_deal_is_good(self):
        self.assertEqual(analyze(Inputs(monthly_rent=2600)).verdict, "Good")

    def test_to_monthly(self):
        self.assertAlmostEqual(to_monthly(1200, "year"), 100)
        self.assertAlmostEqual(to_monthly(100, "month"), 100)
        with self.assertRaises(ValueError):
            to_monthly(100, "week")

    def test_year_and_month_give_same_answer(self):
        """$2,400/yr tax == $200/mo tax, $1,200/yr insurance == $100/mo, etc."""
        yearly = analyze(Inputs(
            property_tax=2400, property_tax_period="year",
            insurance=1200, insurance_period="year",
            hoa=600, hoa_period="year",
            utilities=1800, utilities_period="year",
            other_costs=360, other_costs_period="year"))
        monthly = analyze(Inputs(
            property_tax=200, property_tax_period="month",
            insurance=100, insurance_period="month",
            hoa=50, hoa_period="month",
            utilities=150, utilities_period="month",
            other_costs=30, other_costs_period="month"))
        self.assertAlmostEqual(yearly.operating_expenses, monthly.operating_expenses)
        self.assertAlmostEqual(yearly.cash_flow_monthly, monthly.cash_flow_monthly)
        for line in ("Property tax", "Insurance", "HOA", "Utilities", "Other"):
            self.assertAlmostEqual(yearly.breakdown[line], monthly.breakdown[line])
        # Worked example + $50 HOA + $150 utilities + $30 other = $230 more per month
        self.assertAlmostEqual(monthly.cash_flow_monthly, 183.52 - 230, places=2)

    def test_period_choice_changes_result(self):
        """$100 HOA per month costs 12x more than $100 HOA per year."""
        per_month = analyze(Inputs(hoa=100, hoa_period="month"))
        per_year = analyze(Inputs(hoa=100, hoa_period="year"))
        self.assertAlmostEqual(per_month.breakdown["HOA"], 100)
        self.assertAlmostEqual(per_year.breakdown["HOA"], 100 / 12)

    def test_zero_interest(self):
        self.assertAlmostEqual(monthly_payment(120_000, 0, 10), 1000)


if __name__ == "__main__":
    unittest.main()
