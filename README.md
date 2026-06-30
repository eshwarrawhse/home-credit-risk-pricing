# Home Credit Risk-Based Loan Pricing

Every applicant in this loan portfolio gets the same interest rate, regardless of how likely they are to default. The safest borrowers subsidise the riskiest ones, and a competitor who prices by risk can undercut the lender on the customers they most want to keep. This project builds a risk-tiered pricing policy that addresses both problems — and documents, honestly, the three attempts it took to get it right.

---

## The Story (Three Iterations)

### Iteration 1 — The Obvious Idea, and Why It Lost Money

The starting point was straightforward: segment borrowers into 5 risk tiers using a logistic regression on income, credit amount, age, employment length, and debt-to-income ratios. Score every applicant, assign tiers by quintile of predicted default probability, charge higher rates to riskier tiers.

The model separated default behaviour cleanly:

| Tier | Actual Default Rate |
|---|---|
| Tier 1 (Lowest Risk) | 4.7% |
| Tier 2 | 6.8% |
| Tier 3 | 8.4% |
| Tier 4 | 10.5% |
| Tier 5 (Highest Risk) | 12.9% |

But when I ran the revenue simulation — holding volume fixed and applying the new rates — **tiered pricing lost 15.7% of revenue versus the flat baseline.** The reason: a risk-based pricing model prices Tier 1 applicants lower and Tier 5 applicants higher, but Tier 5's elevated default rate eats more of the interest income than the rate hike recovers, and Tier 1's lower rate gives away revenue without any offsetting gain. Volume-fixed pricing is the wrong framing entirely.

### Iteration 2 — Added Elasticity, Got the Revenue, Missed the Point

The second version added price elasticity: if you raise Tier 5's rate, fewer borrowers accept the loan. The volume loss offsets some of the rate gain. Similarly, lowering Tier 1's rate might attract more borrowers. With literature-anchored semi-elasticities (−8%/pt for safest, −20%/pt for riskiest, with a demand kink past +3pt for the highest-risk tier), the optimizer found rates for each tier that maximised within-tier net revenue.

This produced a +3.2% portfolio revenue lift. It also introduced a policy guardrail: freeze Tier 1 and Tier 2 at the flat rate, raise Tier 3-5 only.

**The problem:** freezing Tier 1-2 at the flat rate doesn't protect those customers from a competitor who is already offering them 12% instead of 14%. It just leaves their rate exactly as exposed as before, while claiming credit for a retention argument that the policy doesn't actually implement. The +3.2% was real arithmetic; the reasoning behind it was circular.

### Iteration 3 — Corrected Approach: Separate the Optimizer from the Policy

The third version re-ran the elasticity optimizer with no tier frozen. The result was immediately informative: **the optimizer never recommends discounting Tier 1-2 on its own.** It wants to raise every tier's rate, because the within-tier elasticity model only captures borrowers who decline *our* offer — it has no concept of a competitor poaching our safest customers by offering them a sharper rate.

That gap proves the discount cannot come from the model. It has to come from an explicitly stated business judgment: **Customer Lifetime Value (CLV) and competitive retention economics.** Lending research treats retaining a low-risk customer as more valuable than a single loan cycle's interest margin, because acquisition costs more than retention and a safe customer retained across multiple loan cycles compounds over time.

The final policy applies a 1-point discount to Tier 1-2 as a stated policy assumption (not a model output), and applies the elasticity-optimized rate to Tier 3-5. The memo in `/docs` states this explicitly, calculates its year-one cost, and explains exactly what evidence would be needed to validate it.

---

## Final Numbers

| Tier | Default Rate | Recommended Rate | vs. Flat (14%) | Net Revenue | Lift vs. Flat |
|---|---|---|---|---|---|
| Tier 1 (Lowest Risk) | 4.7% | 13.0% | −1.0pt (policy discount) | ₹3,955M | −₹149M |
| Tier 2 | 6.8% | 13.0% | −1.0pt (policy discount) | ₹2,482M | −₹140M |
| Tier 3 | 8.4% | 15.5% | +1.5pt (elasticity-optimized) | ₹1,732M | +₹65M |
| Tier 4 | 10.5% | 15.5% | +1.5pt (elasticity-optimized) | ₹932M | +₹89M |
| Tier 5 (Highest Risk) | 12.9% | 16.0% | +2.0pt (elasticity-optimized) | ₹367M | +₹149M |
| **Portfolio Total** | | | | **₹9,468M** | **+₹13.7M (+0.1%)** |

**The honest headline is that this policy is approximately revenue-neutral in year one.** The ₹303M gained on Tiers 3-5 nearly exactly offsets the ₹289M cost of discounting Tiers 1-2. The strategic case rests on multi-year retention value that this dataset cannot measure.

---

## Limitations

These are stated upfront, not buried.

- **Elasticity is not measured from this data.** The semi-elasticities used are literature-anchored assumptions. The actual dataset has no pricing experiment in it. These numbers are directionally reasonable; they are not empirically calibrated to Home Credit's real borrowers.
- **Model AUC is modest (~0.61).** The logistic regression uses 9 features and is intentionally simple. The point of the model is risk *segmentation*, not prediction accuracy — the tiers need to separate default rates meaningfully, which they do. Replacing it with a gradient-boosted model would sharpen the tiers but wouldn't change the pricing framework.
- **No adverse selection modelling within tiers.** Raising Tier 5's rate may attract the riskiest applicants *within* Tier 5 (the ones with no better option), pushing the realised default rate above the historical 12.9% we measured at the old rate. This could erode the Tier 5 revenue gain. The pilot plan tracks this explicitly.
- **No CLV data in scope.** The Tier 1-2 discount argument depends on multi-year retention value that lives in repeat-borrowing history (Home Credit's `bureau.csv` and `previous_application.csv`). That data is out of scope here. The discount is justified as an assumption, not a calculated value.

---

## What I'd Do Next

The entire value case for this policy rests on a retention assumption we have not tested. The natural next step is a controlled pilot designed specifically to generate the evidence this memo depends on:

1. **Measure real elasticity (Tier 3-5 A/B test).** Run new applicants randomly to the tiered rate vs. flat, measure take-up by tier. This replaces the literature assumption with an actual estimate from our customer base.
2. **Measure retention value (Tier 1-2 A/B test with a long follow-up window).** Run the discounted rate against flat, and track repeat-borrowing and customer tenure over 2-3 loan cycles. This is the only way to find out whether the ₹289M annual cost is worth paying.
3. **Watch for adverse selection in Tier 5.** Monitor realised default rates during the pilot; if Tier 5 breaches its historical baseline by more than 1pp, revert immediately.

These are business/product experiments, not modelling iterations. The model is good enough; what this project is missing is real pricing data.

---

## Repo Structure

```
home-credit-risk-pricing/
├── scripts/
│   └── risk_pricing_analysis.py   # full analysis: model → tiers → pricing simulation → charts
├── docs/
│   └── strategy_memo.md           # internal strategy memo written alongside the analysis
├── charts/                        # generated by the script (3 PNGs)
├── data/                          # empty — dataset not included (see below)
├── requirements.txt
└── .gitignore
```

---

## Setup & Running

**Dataset:** Download `application_train.csv` from the [Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk/data) competition on Kaggle. Place it at `data/application_train.csv`.

```bash
# 1. Clone and enter the repo
git clone repo
cd home-credit-risk-pricing

# 2. Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Place the dataset
# data/application_train.csv  ← put it here

# 4. Run the analysis
python scripts/risk_pricing_analysis.py

# Charts are saved to ./charts/
```

The script prints tier validation, optimizer output, and the full revenue comparison to stdout. Runtime is ~2 minutes on a standard laptop.
