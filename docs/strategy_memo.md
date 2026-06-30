# Strategy Memo: Risk-Based Loan Pricing Policy (v2 — Revised)

**To:** Head of Risk & Growth
**From:** Eshwar Baskaran, Product (Risk Strategy)
**Re:** Moving from flat-rate to risk-tiered pricing — recommendation, rollout plan, and an honest accounting of what this costs

**Note on this revision:** an earlier draft of this memo proposed freezing Tier 1-2 at today's flat rate while raising Tier 3-5. A review of that draft correctly identified this as a contradiction: we cannot claim to be "protecting safe borrowers from competitive risk" while leaving their price completely unchanged. This version corrects that — Tier 1-2 now receive a real discount, and this memo states plainly what that discount costs and why we believe it's worth paying.

---

## TL;DR

Move from a single flat interest rate to a 5-tier risk-based pricing structure. Tier 1-2 (our safest, highest-volume, most competitively contestable customers) get a genuine 1-point rate cut. Tier 3-5 move to elasticity-aware higher rates. **Net effect in year one: approximately breakeven (+0.1% vs flat, ~₹13.7M on a ₹9.45B base).** This is not a revenue-growth pitch. The case for this policy rests on a benefit we cannot measure from this dataset — multi-year customer retention value — and this memo says so explicitly rather than disguising a retention bet as a revenue projection.

## 1. The Problem

Today, every approved borrower is priced at the same flat rate regardless of default risk. Two consequences:

- **Safe borrowers have no price protection.** A competitor with sharper risk-based pricing can offer them a materially better rate than ours, and we have no lever to respond.
- **Risky borrowers are underpriced relative to their loss rate.** Our highest-risk tier defaults at 12.9% — nearly 3x our lowest tier (4.7%) — at an identical rate.

## 2. What We Tried First, and Why It Was Wrong (Twice)

**Attempt 1:** Tiered pricing assuming volume stays fixed regardless of rate. Result: -15.7% to -16.2% revenue versus flat. Wrong because it ignored that customers respond to price changes at all.

**Attempt 2:** Added elasticity, but froze Tier 1-2 at the flat rate as a "guardrail" while letting Tier 3-5 increase. This produced a clean-looking +3.2% revenue lift — but it didn't actually solve the problem stated in Section 1. Freezing a price doesn't defend it from a competitor undercutting it; it just leaves it exactly as exposed as before. **The +3.2% number in that version was real, but the policy behind it didn't do what we said it would do.** Worth naming directly: that's the kind of gap that looks fine in a spreadsheet and falls apart the moment someone asks "wait, how does keeping the rate the same protect anyone?"

## 3. The Corrected Approach

We re-ran the elasticity-adjusted optimizer with no freeze on any tier. The result is informative on its own: **left alone, the optimizer never recommends discounting Tier 1-2 — it wants to raise every tier's rate**, because our within-tier elasticity model only captures customers leaving *us*, not customers being poached by a *competitor*. The model has no concept of competitive risk; it only knows about our own demand curve.

That is the proof that a Tier 1-2 discount cannot come from this model. It has to come from a separate, explicitly stated business judgment: **Customer Lifetime Value (CLV) and retention economics.** Lending industry practice treats retaining an existing low-risk customer as more valuable than the interest earned on a single loan cycle, because acquiring a replacement customer costs more than retaining one, and a low-risk customer retained across multiple loan cycles compounds in value over time. We do not have the repeat-borrowing data in this dataset to calculate a precise CLV multiple for Home Credit's actual customers — that lives in transaction history we didn't pull into scope. So this is presented as exactly what it is: a stated policy assumption with a transparently calculated cost, not a model-derived number.

## 4. The Recommendation

| Tier | Default Rate | Recommended Rate | vs. Flat (14%) | Net Revenue | Lift vs. Flat |
|---|---|---|---|---|---|
| Tier 1 (Lowest Risk) | 4.7% | **13.0%** | -1.0pt (policy discount) | ₹3,955M | -₹149M |
| Tier 2 | 6.8% | **13.0%** | -1.0pt (policy discount) | ₹2,482M | -₹140M |
| Tier 3 | 8.4% | **15.5%** | +1.5pt (elasticity-optimized) | ₹1,732M | +₹65M |
| Tier 4 | 10.5% | **15.5%** | +1.5pt (elasticity-optimized) | ₹932M | +₹89M |
| Tier 5 (Highest Risk) | 12.9% | **16.0%** | +2.0pt (elasticity-optimized) | ₹367M | +₹149M |
| **Portfolio Total** | | | | **₹9,468M** | **+₹13.7M (+0.1%)** |

**The honest headline: this policy is approximately revenue-neutral in year one.** The ₹303M gained from Tiers 3-5 nearly exactly offsets the ₹289M cost of discounting Tiers 1-2. That is not a coincidence we engineered — it's what happens when you actually price a genuine retention discount instead of getting it for free by freezing a rate.

**The strategic case for proceeding anyway:** the ₹289M cost buys something the year-one P&L can't show — the retained lifetime value of our most creditworthy, highest-volume customer segment, against a competitor who may already be pricing more sharply. If that retention value is real, this policy pays for itself over multiple loan cycles even though it doesn't pay for itself in year one. If it isn't real — if Tier 1-2 customers are not actually price-sensitive enough to be at competitive risk — then we are paying ₹289M for a discount nobody needed. **We do not currently know which of these is true, and this memo does not pretend otherwise.** Section 6 proposes how we find out before committing fully.

## 5. What We're Explicitly Not Claiming

- **We have not measured our actual customers' elasticity.** Tier 3-5 rates are directionally sound, literature-anchored, not precisely calibrated to Home Credit's real customers.
- **We have not measured Tier 1-2's actual competitive exposure or retention sensitivity.** The 1-point discount and its ₹289M cost are real arithmetic; the *justification* for paying that cost is a stated assumption, not a derived result. This is the single biggest open question in this memo, and Phase 2 below is designed specifically to close it.
- **We have not modeled adverse selection within a tier.** Raising Tier 5's rate may not just reduce volume — it could shift who remains toward the riskiest applicants within that tier, pushing true Tier 5 default rate above the 12.9% we measured at the old rate. If that happens, the +₹149M Tier 5 gain could be partially or fully offset by higher-than-modeled losses. This needs to be tracked explicitly in the pilot, not assumed away.

## 6. Rollout Plan

**Phase 1 — Shadow Mode (4 weeks).** Calculate what each new applicant would be priced under the new policy; log it without acting on it. Compare shadow-quoted Tier 1-2 rates against any publicly available competitor rate data as a directional sanity check.

**Phase 2 — Controlled Pilot (8 weeks). This phase is now the most important part of this plan, because it's the only way to test the actual assumption this policy depends on.**
- Tier 3-5: A/B test tiered vs. flat rates on new applicants, measuring real take-up by tier — this gives us our first real elasticity estimate, replacing the literature-anchored assumption.
- Tier 1-2: A/B test the discounted rate vs. flat on new applicants, and **track downstream retention/repeat-borrowing over the following 2-3 loan cycles**, not just immediate take-up. This is the only way to start validating whether the CLV argument in Section 3 is actually true for our customers, or whether we're paying for a benefit that doesn't materialize.

**Success criteria:** tiered group shows revenue performance in line with or better than this memo's projection, without any tier's default rate exceeding its historical baseline by more than 1 percentage point, and with early signal that Tier 1-2 retention/repeat-borrowing trends upward versus the flat-rate control group.

**Rollback trigger:** any tier's default rate breaches that threshold, or take-up diverges sharply from what our elasticity assumption predicted — revert that tier to flat pricing immediately.

**Phase 3 — Full Rollout.** Only after Phase 2 gives us real elasticity and real early retention signal — not before, since this entire policy's value case currently rests on an assumption we have not yet tested.

## 7. The One-Sentence Summary for a Skeptical Reader

We are not claiming this makes more money next year. We are claiming it's close to free to find out whether it makes more money over the following several years — and we've built a pilot specifically designed to answer that, rather than asking for a full rollout on faith.
