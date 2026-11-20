"""Rental Cash-Flow Calculator - desktop app (Tkinter, comes with Python).

Run:  python app.py
Results update live as you type.
"""
import tkinter as tk
from tkinter import font as tkfont
from dataclasses import asdict

from calculator import Inputs, analyze, input_names

# ---------- Look & feel ----------
BG = "#0f172a"        # page background
PANEL = "#1e293b"     # cards
PANEL_2 = "#273449"   # input boxes
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
GOOD = "#22c55e"
OK = "#f59e0b"
POOR = "#ef4444"
VERDICT_COLORS = {"Good": GOOD, "OK": OK, "Poor": POOR}
BAR_COLORS = ["#38bdf8", "#818cf8", "#f472b6", "#fb923c", "#a3e635",
              "#2dd4bf", "#facc15", "#c084fc", "#f87171", "#94a3b8"]

PERIOD = object()  # marker: this field gets a period dropdown
PERIOD_LABELS = {"year": "per year", "month": "per month"}
PERIOD_FROM_LABEL = {v: k for k, v in PERIOD_LABELS.items()}

# (section title, [(field name, label, unit hint)])
SECTIONS = [
    ("Purchase & Loan", [
        ("purchase_price", "Purchase price", "$"),
        ("down_payment_pct", "Down payment", "%"),
        ("closing_costs", "Closing costs", "$"),
        ("rehab_costs", "Repairs before renting", "$"),
        ("interest_rate", "Interest rate", "% / yr"),
        ("loan_term_years", "Loan term", "years"),
        ("pmi_rate", "PMI (if down < 20%)", "% / yr"),
    ]),
    ("Income", [
        ("monthly_rent", "Monthly rent", "$ / mo"),
        ("other_income", "Other income", "$ / mo"),
        ("vacancy_pct", "Vacancy", "% of rent"),
    ]),
    # PERIOD = show a "per year / per month" dropdown instead of a fixed unit
    ("Fixed Expenses", [
        ("property_tax", "Property tax", PERIOD),
        ("insurance", "Insurance", PERIOD),
        ("hoa", "HOA fees", PERIOD),
        ("utilities", "Utilities (owner pays)", PERIOD),
        ("other_costs", "Other (lawn, pest...)", PERIOD),
    ]),
    ("Percent-of-Rent Expenses", [
        ("maintenance_pct", "Maintenance / repairs", "% of rent"),
        ("capex_pct", "CapEx (roof, HVAC...)", "% of rent"),
        ("management_pct", "Property management", "% of rent"),
    ]),
]


def money(x: float) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x):,.0f}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rental Cash-Flow Calculator")
        self.configure(bg=BG)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{int(sw * 0.92)}x{int(sh * 0.85)}+{int(sw * 0.04)}+20")
        try:
            self.state("zoomed")  # open maximized on Windows
        except tk.TclError:
            pass

        base = tkfont.nametofont("TkDefaultFont").actual("family")
        self.f_title = (base, 20, "bold")
        self.f_section = (base, 11, "bold")
        self.f_label = (base, 10)
        self.f_small = (base, 9)
        self.f_value = (base, 16, "bold")
        self.f_verdict = (base, 30, "bold")

        self.vars: dict[str, tk.StringVar] = {}
        self.period_vars: dict[str, tk.StringVar] = {}  # e.g. "hoa" -> "per month"
        self._build_header()
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_inputs(body)
        self._build_results(body)
        self.recalculate()

    # ---------- Header ----------
    def _build_header(self):
        h = tk.Frame(self, bg=BG)
        h.pack(fill="x", padx=20, pady=(16, 12))
        tk.Label(h, text="🏠  Rental Cash-Flow Calculator", font=self.f_title,
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Button(h, text="Reset to defaults", command=self.reset,
                  bg=PANEL_2, fg=TEXT, activebackground=ACCENT, activeforeground=BG,
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  font=self.f_label).pack(side="right")

    # ---------- Left: inputs ----------
    def _build_inputs(self, parent):
        outer = tk.Frame(parent, bg=PANEL)
        outer.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        canvas = tk.Canvas(outer, bg=PANEL, highlightthickness=0, width=360)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=PANEL)
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all"), width=inner.winfo_reqwidth()))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.bind_all("<MouseWheel>",
                      lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        defaults = asdict(Inputs())
        for title, items in SECTIONS:
            tk.Label(inner, text=title.upper(), font=self.f_section, bg=PANEL,
                     fg=ACCENT, anchor="w").pack(fill="x", padx=18, pady=(16, 6))
            for name, label, unit in items:
                row = tk.Frame(inner, bg=PANEL)
                row.pack(fill="x", padx=18, pady=3)
                tk.Label(row, text=label, font=self.f_label, bg=PANEL, fg=TEXT,
                         anchor="w", width=22).pack(side="left")
                if unit is PERIOD:
                    self._period_dropdown(row, name, defaults[name + "_period"])
                else:
                    tk.Label(row, text=unit, font=self.f_small, bg=PANEL, fg=MUTED,
                             width=10, anchor="w").pack(side="right")
                v = tk.StringVar(value=self._fmt_default(defaults[name]))
                v.trace_add("write", lambda *_: self.recalculate())
                e = tk.Entry(row, textvariable=v, width=11, justify="right",
                             bg=PANEL_2, fg=TEXT, insertbackground=TEXT,
                             relief="flat", font=self.f_label,
                             highlightthickness=1, highlightbackground=PANEL_2,
                             highlightcolor=ACCENT)
                e.pack(side="right", ipady=4, padx=(6, 6))
                self.vars[name] = v
        tk.Label(inner, text="Tip: results update as you type.", font=self.f_small,
                 bg=PANEL, fg=MUTED).pack(anchor="w", padx=18, pady=(14, 18))

    def _period_dropdown(self, row, name, default_period):
        pv = tk.StringVar(value=PERIOD_LABELS[default_period])
        pv.trace_add("write", lambda *_: self.recalculate())
        menu = tk.OptionMenu(row, pv, *PERIOD_LABELS.values())
        menu.config(bg=PANEL_2, fg=TEXT, activebackground=ACCENT, activeforeground=BG,
                    relief="flat", highlightthickness=0, bd=0, font=self.f_small,
                    width=8, anchor="w", cursor="hand2")
        menu["menu"].config(bg=PANEL_2, fg=TEXT, activebackground=ACCENT,
                            activeforeground=BG, font=self.f_small)
        menu.pack(side="right")
        self.period_vars[name] = pv

    @staticmethod
    def _fmt_default(x):
        return f"{x:g}"

    # ---------- Right: results ----------
    def _build_results(self, parent):
        right = tk.Frame(parent, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        # Verdict banner
        self.banner = tk.Frame(right, bg=PANEL)
        self.banner.grid(row=0, column=0, sticky="ew")
        self.banner_stripe = tk.Frame(self.banner, width=10, bg=GOOD)
        self.banner_stripe.pack(side="left", fill="y")
        bl = tk.Frame(self.banner, bg=PANEL)
        bl.pack(side="left", fill="both", expand=True, padx=18, pady=12)
        tk.Label(bl, text="VERDICT", font=self.f_small, bg=PANEL, fg=MUTED,
                 anchor="w").pack(fill="x")
        self.verdict_lbl = tk.Label(bl, text="", font=self.f_verdict, bg=PANEL,
                                    fg=GOOD, anchor="w")
        self.verdict_lbl.pack(fill="x")
        self.reasons_frame = tk.Frame(bl, bg=PANEL)
        self.reasons_frame.pack(fill="x", pady=(4, 0))

        # Metric cards
        grid = tk.Frame(right, bg=BG)
        grid.grid(row=1, column=0, sticky="ew", pady=14)
        cards = [
            ("cf_m", "Monthly cash flow", "What's left each month"),
            ("cf_y", "Yearly cash flow", "Monthly × 12"),
            ("pi", "Mortgage (P&I)", "Principal + interest / mo"),
            ("exp", "Total expenses", "All costs / mo incl. loan"),
            ("noi", "NOI (yearly)", "Income − operating costs"),
            ("cap", "Cap rate", "NOI ÷ price"),
            ("coc", "Cash-on-cash", "Yearly cash flow ÷ cash in"),
            ("one", "1% rule", "Rent ÷ price (want ≥ 1%)"),
            ("cash", "Cash needed", "Down + closing + repairs"),
            ("dscr", "DSCR", "NOI ÷ loan payments"),
        ]
        self.card_vals = {}
        cols = 5
        for c in range(cols):
            grid.columnconfigure(c, weight=1, uniform="cards")
        for idx, (key, title, hint) in enumerate(cards):
            card = tk.Frame(grid, bg=PANEL)
            card.grid(row=idx // cols, column=idx % cols, sticky="nsew",
                      padx=(0 if idx % cols == 0 else 10), pady=(0 if idx < cols else 10))
            tk.Label(card, text=title, font=self.f_small, bg=PANEL, fg=MUTED,
                     anchor="w").pack(fill="x", padx=12, pady=(10, 0))
            val = tk.Label(card, text="", font=self.f_value, bg=PANEL, fg=TEXT, anchor="w")
            val.pack(fill="x", padx=12)
            tk.Label(card, text=hint, font=self.f_small, bg=PANEL, fg=MUTED,
                     anchor="w").pack(fill="x", padx=12, pady=(0, 10))
            self.card_vals[key] = val

        # Where the rent goes (bar chart)
        chart_card = tk.Frame(right, bg=PANEL)
        chart_card.grid(row=2, column=0, sticky="nsew")
        right.rowconfigure(2, weight=1)
        tk.Label(chart_card, text="WHERE THE MONEY GOES  (per month)", font=self.f_section,
                 bg=PANEL, fg=ACCENT, anchor="w").pack(fill="x", padx=16, pady=(12, 4))
        self.chart = tk.Canvas(chart_card, bg=PANEL, highlightthickness=0, height=260)
        self.chart.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.chart.bind("<Configure>", lambda e: self._draw_chart())
        self._last = None

    # ---------- Logic ----------
    def _read_inputs(self):
        vals = {}
        for name, v in self.vars.items():
            txt = v.get().replace(",", "").replace("$", "").replace("%", "").strip()
            try:
                vals[name] = float(txt) if txt else 0.0
            except ValueError:
                return None
        for name, pv in self.period_vars.items():
            vals[name + "_period"] = PERIOD_FROM_LABEL[pv.get()]
        return Inputs(**vals)

    def recalculate(self):
        if len(self.vars) < len(input_names()) or not hasattr(self, "chart"):
            return  # still building the form
        inp = self._read_inputs()
        if inp is None:
            self.verdict_lbl.config(text="Check your numbers", fg=OK)
            return
        r = analyze(inp)
        self._last = r

        color = VERDICT_COLORS[r.verdict]
        self.verdict_lbl.config(text=r.verdict, fg=color)
        self.banner_stripe.config(bg=color)
        for w in self.reasons_frame.winfo_children():
            w.destroy()
        for ok, text in r.reasons:
            icon, c = ("✔", GOOD) if ok is True else ("●", OK) if ok is None else ("✖", POOR)
            row = tk.Frame(self.reasons_frame, bg=PANEL)
            row.pack(fill="x")
            tk.Label(row, text=icon, font=self.f_label, bg=PANEL, fg=c, width=2).pack(side="left")
            tk.Label(row, text=text, font=self.f_label, bg=PANEL, fg=TEXT,
                     anchor="w").pack(side="left")

        cf_color = GOOD if r.cash_flow_monthly >= 200 else OK if r.cash_flow_monthly >= 0 else POOR
        cv = self.card_vals
        cv["cf_m"].config(text=money(r.cash_flow_monthly), fg=cf_color)
        cv["cf_y"].config(text=money(r.cash_flow_yearly), fg=cf_color)
        cv["pi"].config(text=money(r.mortgage_pi))
        cv["exp"].config(text=money(r.total_expenses))
        cv["noi"].config(text=money(r.noi_yearly))
        cv["cap"].config(text=f"{r.cap_rate:.2f}%")
        cv["coc"].config(text=f"{r.cash_on_cash:.2f}%",
                         fg=GOOD if r.cash_on_cash >= 8 else OK if r.cash_on_cash >= 4 else POOR)
        cv["one"].config(text=f"{r.rent_to_price:.2f}%",
                         fg=GOOD if r.rent_to_price >= 1 else POOR)
        cv["cash"].config(text=money(r.cash_invested))
        dscr_txt = "∞" if r.dscr == float("inf") else f"{r.dscr:.2f}"
        cv["dscr"].config(text=dscr_txt,
                          fg=GOOD if r.dscr >= 1.25 else OK if r.dscr >= 1 else POOR)
        self._draw_chart()

    def _draw_chart(self):
        r = self._last
        c = self.chart
        c.delete("all")
        if r is None:
            return
        w = max(c.winfo_width(), 300)
        items = [(k, v) for k, v in r.breakdown.items() if v > 0.005]
        if r.vacancy_loss > 0.005:
            items.append(("Vacancy loss", r.vacancy_loss))
        items.sort(key=lambda kv: -kv[1])
        if r.cash_flow_monthly > 0:
            items.append(("Your cash flow", r.cash_flow_monthly))
        if not items:
            return
        top = max(v for _, v in items)
        label_w, value_w = 150, 80
        bar_max = max(w - label_w - value_w, 40)
        row_h = max(min(36,(c.winfo_height() - 4) // max(len(items), 1)), 14)
        for i, (name, val) in enumerate(items):
            y = i * row_h + 2
            color = GOOD if name == "Your cash flow" else BAR_COLORS[i % len(BAR_COLORS)]
            c.create_text(0, y + row_h / 2, text=name, anchor="w", fill=TEXT, font=self.f_small)
            bw = bar_max * val / top
            c.create_rectangle(label_w, y + 4, label_w + bw, y + row_h - 4,
                               fill=color, outline="")
            c.create_text(label_w + bw + 8, y + row_h / 2, text=money(val),
                          anchor="w", fill=MUTED, font=self.f_small)

    def reset(self):
        defaults = asdict(Inputs())
        for name, var in self.vars.items():
            var.set(self._fmt_default(defaults[name]))
        for name, pv in self.period_vars.items():
            pv.set(PERIOD_LABELS[defaults[name + "_period"]])


if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)  # sharp text on Windows
    except Exception:
        pass
    App().mainloop()
