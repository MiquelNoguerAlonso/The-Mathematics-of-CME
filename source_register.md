# Operational source register

All operational sources were read on September 11, 2026 (UTC). Bibliographic year 2026 denotes the consultation snapshot, not an assertion that every page was originally published in 2026. URLs and titles are in references.bib. The project does not redistribute exchange specifications.

| Key | Material used | Scope in this paper |
|---|---|---|
| CMEMatching | Supported algorithm families; SOFR opening and residual branches | Distinguish FIFO, proportional, priority and configurable mechanisms |
| CMESteps | Algorithm matrix; FIFO modification rules; PR minimum; displayed quantity | Exact model of a PR stage followed by FIFO; no LMM percentage assumptions |
| CMEImplied | Implied IN/OUT; shared input orders; matching/visibility limitations | Algebra and integer resource constraints for declared recipes |
| CMEIOPRules | Maximum quantity, imbalance cases, reference, iterative stop election | Verified opening branches; remaining exact ties are deliberately set-valued |
| CMEIOPExamples | Mixed zero/nonzero imbalance example; same-side pressure; balanced interval | Synthetic opening cases independent of published numerical examples |
| CMEMDP | Futures/options data views and security status | Observations are projections of mechanism state |
| CMEMBO | New/update/delete; price-side-local priority; event completion; no implied MBO | Conditions for reconstructing the disseminated book |
| CMEEvents | Event grouping and MatchEventIndicator; invisible stop events | Do not interpret a partial event as a completed book |
| CMESettlements | Product-specific procedures and exceptional determinations | A daily settlement is a rule-defined statistic |
| CMESettleES | Lead ES month VWAP window and quarter-point rounding; final SOQ | Worked ordinary lead-month example; no extrapolation to all contracts |
| CMEMoney | Normal futures rounding; trade/position variation; premium conventions | A rounded money-value map; excludes inverse and special notional conventions |
| CMESPAN2 | Historical/stress, liquidity and concentration components | Motivation only; the convex illustration is not SPAN 2 |
| CMERisk | SPAN/SPAN 2 coexistence in public overview | No unsupported claim of universal migration |
| CMESafeguards | Regular cycles and default waterfall architecture | Cycle indexing and a stylized tranche loss map; no production resource amounts |
| CMECollateral | Member versus client collateral standards; account restrictions | Eligibility- and deadline-sensitive resource allocation |
| CMEAcceptable | Asset eligibility, haircut and cap structure | All numerical haircuts in the example are synthetic |
| CME358 | ES value factor, outright/spread increments, trading-day close, final settlement | Contract dimensions and cash versus notional distinction |
| CME358A | One underlying futures contract per option; premium units; series conventions | Exercise ledger with explicitly specified conventions |
| NYMEX200 | CL unit, price tick and physical delivery at Cushing | Spread unit conversions and delivery feasibility |
| CBOT19 | Treasury unit/ticks; conversion-factor invoice; deliverable basket | Synthetic fixed-date cheapest-to-deliver comparison |

Mathematical tools are standard. The paper proves the stated finite-dimensional results directly and attributes convex optimization and the CVaR representation to their established literature. Production algorithm configurations, migration schedules, live margins, customer agreements, legal account eligibility, market-impact calibration and complete protocol recovery are not reconstructed by this project.
