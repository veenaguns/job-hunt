# Rental Cash-Flow Calculator

A desktop app that tells you if buying a house and renting it out makes money each month.
It uses only built-in Python (Tkinter), so there is nothing extra to install.

## How to run (Windows)

1. Open PowerShell in this folder.
2. Run:

```powershell
python app.py
```

Type in any box. The results update right away. **Reset to defaults** brings back the starting numbers.

## What you can change

- **Purchase & loan:** price, down payment %, closing costs, repairs before renting, interest rate, loan term, PMI
- **Income:** monthly rent, other income (parking, laundry), vacancy %
- **Fixed expenses:** property tax, insurance, HOA, utilities you pay, other (lawn, pest control).
  Each has a **per year / per month** dropdown. Pick whichever matches the number you have (e.g. a tax bill is yearly, an HOA fee is often monthly). The app converts it for you.
- **Percent-of-rent expenses:** maintenance, CapEx (savings for big repairs like a roof), property management

## What it shows

- Mortgage payment (P&I = principal + interest), total monthly expenses
- Monthly and yearly cash flow (money left after every bill)
- NOI (net operating income: rent minus running costs, not counting the loan)
- Cap rate, cash-on-cash return, DSCR (can the rent cover the loan?), cash needed
- 1% rule check (rent should be at least 1% of the price)
- A **Good / OK / Poor** verdict with reasons, and a chart of where the rent goes

**Verdict rules** (common investor rules of thumb, not laws):

| Check | Good | OK |
|---|---|---|
| Monthly cash flow | $200+ | $0+ |
| Cash-on-cash return | 8%+ | 4%+ |
| DSCR | 1.25+ | 1.0+ |
| 1% rule | pass | — |

Losing money each month, or DSCR under 1.0, is always **Poor**.

## Checking the math

```powershell
python -m unittest -v
```

`test_calculator.py` holds a worked example done by hand with the default numbers:
$200,000 house, 20% down, 7% for 30 years, $2,000 rent → $1,064.48 mortgage, $183.52/month cash flow, 7.49% cap rate, 4.79% cash-on-cash → **OK**.

## Files

- `app.py` — the window you see
- `calculator.py` — all the math (no screen code)
- `test_calculator.py` — the worked example as tests
