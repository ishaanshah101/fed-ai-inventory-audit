# Preregistration

**Study.** An audit of the 2025 Federal AI Use Case Inventory: what the United States
government says it has bought and built, whether the entries are complete, whether a
blinded reader applying the government's own definition of high-impact AI agrees with
the agencies' self-determinations, and whether any of it carries evidence of performance.

**Status.** Written on 26 September 2026 after the structured fields of the inventory
were profiled and before any free-text field was read for rating, before any keyword or
numeral screen was run, before any year-over-year matching, and before any vendor
tabulation. Section 12 states exactly what had been looked at when this was written.
Every later change is a dated, numbered amendment at the bottom.

---

## 1. Why this question

The federal government is the largest single buyer of AI in the world and, since
Executive Order 13960 in 2020, has been required to publish an annual inventory of every
AI use case outside national security. OMB Memorandum M-25-21 (April 2025) rewrote the
governance regime: it defines "high-impact AI" as AI whose output serves as a principal
basis for decisions with legal, material, binding or significant effect on rights,
safety, access to benefits, health, infrastructure or strategic assets; it lists fifteen
categories of use that are presumed high-impact; it requires seven minimum risk
management practices for high-impact AI within 365 days; and it makes the agency itself
the judge of whether a use case is high-impact.

The inventory is therefore a self-report at every level. The agency decides what to list,
what stage it is at, whether it is high-impact, and whether the minimum practices are
done. Nobody outside the agency checks. This study checks the parts that can be checked
from the public text: whether the required fields are filled, whether a reader applying
the memo's own definition blind to the agency's answer reaches the same answer, and
whether the descriptions carry any measurable claim of performance.

## 2. Research questions

- **RQ1 (completeness).** What fraction of inventory entries fill the fields the OMB
  reporting instructions mark as required, and how does that vary by agency?
- **RQ2 (high-impact consistency).** When a blinded reader applies the M-25-21
  definition and presumption list to the free-text description alone, how often does the
  reading agree with the agency's own determination, in which direction do disagreements
  run, and do they concentrate in particular agencies?
- **RQ3 (evidence).** What fraction of deployed or piloted use cases state any numeric
  evidence of performance anywhere in their description?
- **RQ4 (minimum practices).** Of deployed high-impact use cases, what fraction report
  each M-25-21 minimum practice as complete, and how many report all of them?
- **RQ5 (deployment and churn).** What fraction of the inventory is deployed, and what
  fraction of the 2024 inventory's entries can be found in the 2025 inventory at all?
- **RQ6 (vendors).** What share of live use cases were purchased from a vendor, and how
  concentrated is the vendor field?

## 3. Data

- **Source.** OMB's consolidated repository, commit `06c7ebe` (14 May 2026), file
  `Data/2025_individually_reported_AI_use_cases.csv`, 3,611 rows from 41 agencies. This
  is the population of publicly reported individual use cases, not a sample. The 2024
  consolidated inventory (commit `4a29d13`, 2,133 rows) is used for RQ5 only. Both files
  are committed under `data/raw/` with SHA-256 hashes in `results/structured.json`.
- **Unit.** One row, one use case.
- **Live set.** Rows whose `development_stage` is Deployed or Pilot: 1,480 rows. RQ3,
  RQ4 and RQ6 use this set. RQ1 and RQ5 use all rows.

## 4. What the blinded reading records

The rated sample is drawn from the live set and restricted to rows with a non-empty
`problem_solved` or `system_outputs`, since an entry with no description cannot be read.
Sampling, fixed now: every row the agency marked High-impact; every row marked
Presumed-high-impact-but-not; every live row with a blank determination; and from rows
marked Not-high-impact, up to 30 per agency drawn without replacement under seed
20260926. Every sampled row is rated by two of six independent raters.

Raters see only: the use case name, topic area, AI classification, the problem the AI
is intended to solve, the expected benefits, the described outputs, and the data
description. They do not see the agency, bureau, development stage, the agency's
high-impact determination or its justification, the vendor, the PII flag, or any of the
minimum-practice fields. Agency and bureau names and abbreviations are replaced with
`[agency]` in the text. Rows are presented in a seeded shuffle.

**Part A, high-impact reading.** Two judgements.

- `category`: which one of the fifteen presumption categories in M-25-21 Section 6
  (lettered a through o, reproduced verbatim in the rater instructions) the described
  use most closely falls into, or `none`.
- `decision_role`: `principal` if the output is described as determining, or being the
  main basis for, a decision or action about a person, a benefit, an enforcement
  outcome, or physical safety; `assistive` if the output informs, flags, ranks, drafts
  or recommends for a human who makes that decision or takes that action; `none` if no
  such decision or action is described at all.

Derived, fixed now: `reading_high_impact` = `category` is not `none` AND
`decision_role` is not `none`. M-25-21 states that a high-impact determination "is
possible whether there is or is not human oversight," so an assistive role does not
exempt. A stricter variant, `reading_principal_only`, requiring `decision_role` =
`principal`, is reported alongside as a lower bound.

**Part B, evidence of performance.** Five yes-or-no judgements on the text as shown,
identical to the companion audit of AI claims in annual reports: `quantified` (a
specific numeric performance figure is attributed to the AI), `metric_named`,
`evaluation_described` (what data, population or period it was measured over),
`baseline_given`, `uncertainty_given`. Derived: `checkable` = quantified AND
metric_named AND evaluation_described.

**Part C, stage reading.** `in_use` if the text describes the system as currently
operating; `not_yet` if it describes something being built, planned or piloted;
`unclear` otherwise. Compared afterwards to the agency's own `development_stage`.

## 5. Mechanical screens, fixed now

Two exhaustive screens run over the whole relevant population, so that the count they
bound does not depend on which rows happened to be sampled.

- **Presumption keyword screen** over all 3,611 rows: a fixed regular expression per
  presumption category, built from the memo's own words (biometric, facial, fraud,
  eligibility, benefits, diagnosis, patient, recidivism, parole, immigration, asylum,
  hiring, promotion, translation, hazardous, and so on). The pattern list is frozen in
  `src/presumption_screen.py` before it is run. A match is a candidate, not a verdict;
  the blinded reading of sampled rows measures the screen's precision.
- **Numeral screen** over all 1,480 live rows: any percentage, multiple, currency
  amount, magnitude word attached to a digit, or integer of two or more digits in the
  free-text fields. A numeric performance figure is necessary for `quantified`, so this
  gives a hard upper bound on RQ3, and every candidate is read blind.

## 6. Calibration

As in the companion audits, a blinded calibration pass by the orchestrating model
re-reads a seeded, stratified sample of rated rows without the verdicts, with duplicate
controls, and independently reads every numeral-screen candidate. Survival rates are
reported and used to correct the headline rates.

## 7. Year-over-year matching (RQ5)

The 2024 file carries no use case identifier, so matching is by agency and normalised
use case name (lower-cased, punctuation and whitespace collapsed). A 2024 row with no
2025 row of the same agency and name, in any stage including Retired, is counted as
unmatched. That count is an upper bound on silent disappearance, since renamed entries
will not match; a seeded sample of 60 unmatched rows is reviewed by hand against the
agency's full 2025 name list to estimate the rename rate, and the bound is corrected by it.

## 8. Vendor normalisation (RQ6)

`vendor_name` is free text. A fixed normalisation table maps spelling variants and
product names to a parent vendor (for example "Azure OpenAI", "ChatGPT" and "OpenAI"
to OpenAI; "Copilot", "Azure" and "Microsoft" to Microsoft). The table is committed and
every mapping is inspectable. Concentration is reported as the share of vendor-purchased
live use cases held by the top 5 and top 10 vendors.

## 9. Statistics

Proportions over the whole inventory carry no interval, because the inventory is the
population. Proportions estimated from the rated sample carry Wilson intervals and,
where rows cluster within agencies, a percentile bootstrap resampling agencies (10,000
replicates, fixed seed). Agreement between raters is reported as observed agreement and
Krippendorff's alpha for nominal data.

## 10. Who the raters are

Six independent passes of Claude Sonnet, dispatched with the instruction file committed
at `docs/RATER_PROMPT.md` before dispatch. The calibration pass and adjudication are by
Claude Opus 5. No figure here measures human agreement.

## 11. Predictions, stated in advance, on the parts not yet examined

1. The blinded reading will call more sampled rows high-impact than the agencies did:
   among rows the agency marked Not-high-impact, at least 15 percent will read as
   high-impact under the derived rule.
2. Disagreement will concentrate by agency: among agencies with at least 30 live rows,
   the rate at which Not-high-impact rows read as high-impact will be higher at the
   agencies that self-reported zero high-impact live use cases than at the agencies that
   self-reported the most.
3. Fewer than 10 percent of live use cases will state any numeric performance figure,
   and fewer than 2 percent will be checkable.
4. At least 20 percent of 2024 rows will have no name match in 2025.
5. The top 5 vendors will account for more than half of vendor-purchased live use cases.
6. Among rows the agency marked Deployed, at least 10 percent will read as `not_yet` or
   `unclear` on Part C.

## 12. What had already been seen when this was written

The structured-field tabulations in `results/structured.json` were produced before this
document: counts by stage, by self-determination, the agency-by-determination
crosstab for live rows, the minimum-practice fields on deployed high-impact rows, and
the fact that three agencies (Commerce, TVA, Education) submitted no development stage
or determination for any row. No prediction above concerns those tabulations, and RQ1
and RQ4 are reported as description, not as tests. Two free-text rows had been read as
examples during profiling.

## 13. What would falsify the thesis

If the blinded reading agrees with the agencies' determinations at the rate the two
raters agree with each other, and the direction of the few disagreements is balanced,
then agency self-determination under M-25-21 is working as a classification instrument
and that will be reported in those words.

## 14. Amendments

**Amendment 1, 2026-09-26. The numeral screen was extended after unblinding.**
Version 1 of the screen, frozen before it was run, matched percentages, multiples,
currency, magnitude words attached to a digit, and integers of two or more digits,
and produced 208 candidates among the 1,480 live rows. After unblinding, four rows
the automated passes had independently marked `quantified` were found outside the
candidate set: "from about one week to one day", "by a third", "by 2/3", and "within
3-meters". Version 2 adds spelled-out numbers and fractions, slash fractions, and a
single digit attached to a unit, and produces 305 candidates. The 97 added candidates
were read blind under the same protocol and four of them are quantified, exactly the
four the passes had found. Both versions of the screen output are published. The
passes' independent calls are what made the screen's false negatives visible, which
is an argument for keeping a second, non-mechanical detector alongside any screen.

**Amendment 2, 2026-09-26. `is_withheld` is not counted toward completeness.**
The instructions mark it required on the submission to OMB, but in a public inventory
it is trivially "No" for every published row and 1,132 rows omit it. Counting it would
inflate the incompleteness of agencies that dropped a column with no public
information content. It is excluded from the RQ1 denominator.

**Amendment 3, 2026-09-26. Part C did not reproduce and is reported as a negative
result.** The two passes agreed on the stage reading 68 percent of the time with
Krippendorff's alpha of 0.37, and where a pass said `in_use`, the blinded reviewer
agreed on 33 of 150 calibration judgements, reading 114 as `unclear`. The
instruction that present-tense capability without an operational indicator is
`unclear` was not applied consistently by the passes. Prediction 6 is therefore
recorded as untestable as specified, not as held or failed, and the paper reports the
raw pass-level numbers with that caveat.

**Amendment 4, 2026-09-26. The churn review used a shortlist.** Section 7 said each
unmatched 2024 row would be reviewed against the agency's full 2025 name list. For
agencies with several hundred rows that is not a reading task a reviewer can do
reliably, so each row was reviewed against the five 2025 names with the highest
string similarity, and the full list was consulted only when the shortlist looked
wrong. One rename (MTIX) was found outside its shortlist. The rename rate is therefore
a lower bound and the silent-disappearance figure an upper bound, which is how the
paper reports it.

**Amendment 5, 2026-09-26. The vendor normalisation table was written after the
vendor strings were seen.** Section 8 committed to a fixed table but a table cannot be
written before the strings it maps are known. The table was written once, from the
378 distinct strings, and not revised after the concentration figures were computed.
Every mapping is in `results/vendors.json`.

**Note, not an amendment.** The rater instruction was committed to
`docs/RATER_PROMPT.md` before the six passes were dispatched, which the companion
audit of annual reports failed to do and listed as a limitation.
