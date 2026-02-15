# Specialist Validation Directory

This directory contains materials for validating specialist triage decisions against gold standard labels in the clinical evaluation framework.

## Overview

The specialist validation process assesses how well clinical specialists (consultants and registrars) agree with gold standard triage decisions and with each other. The analysis measures:

- **Agreement with gold standard**: Raw agreement rate and Cohen's kappa per specialty
- **Per-category accuracy**: How well each triage level (E/U/R/S) is identified
- **Inter-rater reliability**: Consistency between specialists (Cohen's kappa for pairs, Fleiss' kappa for groups)
- **Cross-level analysis**: Separate metrics for consultant vs registrar performance
- **Disagreement analysis**: Detailed breakdown of mismatches, including ordinal distance and critical disagreements

## Files

### Input

- **specialist_responses.csv**: Main dataset with specialist responses. Expected columns:
  - `specialist_id`: Unique identifier for the specialist
  - `specialty`: Medical specialty (e.g., "cardiology", "neurology")
  - `grade`: Professional grade (e.g., "consultant", "registrar")
  - `case_id`: Case identifier
  - `turn`: Turn number within case
  - `specialist_escalation`: Specialist's triage decision (E/U/R/S, filled in by specialist)
  - `reasoning`: Specialist's written reasoning
  - `author_gold`: Gold standard triage label (E/U/R/S)
  - `agreement`: To be filled in (match/mismatch)

### Output (Generated)

- **specialist_responses_scored.csv**: Copy of input CSV with `agreement` column populated
- **specialist_validation_report.md**: Markdown report with comprehensive analysis results

## Triage Levels

The analysis maps between single-letter codes and full labels:

| Code | Label | Priority |
|------|-------|----------|
| E | emergency_now | Highest (0) |
| U | urgent_same_day | High (1) |
| R | routine_visit | Medium (2) |
| S | self_care | Low (3) |

## Ordinal Distance

When specialists disagree with gold standard, the analysis reports ordinal distance (how far apart the decisions are on the priority scale):

- **1-step**: Adjacent levels (e.g., E vs U, U vs R)
- **2-step**: One level apart (e.g., E vs R, U vs S)
- **3-step**: Maximum distance, flagged as **critical** (E vs S, S vs E)

## Running the Analysis

### Prerequisites

```bash
pip install pandas numpy scikit-learn
```

Note: `scikit-learn` is optional. If not available, the script will fall back to a manual implementation of Cohen's kappa.

### Execution

From this directory:

```bash
python analyse_agreement.py
```

The script will:
1. Load `specialist_responses.csv`
2. Compute per-specialty agreement metrics
3. Calculate inter-rater reliability where applicable
4. Analyze cross-level differences (consultant vs registrar)
5. Identify and categorize disagreements
6. Generate the markdown report
7. Save scored CSV and report

### Output

Progress is printed to stdout. When complete, check:
- `specialist_validation_report.md` for the full analysis
- `specialist_responses_scored.csv` for the dataset with agreement column filled

## Key Metrics

### Raw Agreement
The percentage of cases where specialist label matches gold standard label.

### Cohen's Kappa
Agreement coefficient correcting for chance. Interpretation:
- κ < 0.20: Slight agreement
- 0.21–0.40: Fair agreement
- 0.41–0.60: Moderate agreement
- 0.61–0.80: Substantial agreement
- 0.81–1.00: Almost perfect agreement

### Per-Category Accuracy
For each triage level (E/U/R/S), how often the specialist correctly identified that level when it appeared in the gold standard.

### Inter-Rater Reliability
- **Cohen's kappa** (2 raters per case)
- **Fleiss' kappa** (3+ raters per case)

Measures consistency between specialists rating the same cases.

### Cross-Level Analysis
Separate metrics for consultant and registrar performance, enabling comparison of professional grades.

## Handling Missing Data

The script handles cases where:
- Some specialists haven't filled in responses
- Only 1 specialist has rated a specialty (inter-rater reliability skipped)
- Data is partially complete

Incomplete rows are excluded from analysis. The report logs the number of valid comparisons per specialty.

## Example Report Structure

```markdown
# Specialist Validation Agreement Report

## Summary
- Total specialists: 12
- Total specialties: 8
- Total comparisons: 480
- Disagreements: 45
- Critical disagreements: 2

## Per-Specialty Agreement
### Cardiology
- Specialists: S001, S003, S005
- Comparisons: 60
- Raw agreement: 88.3%
- Cohen's kappa: 0.847 (±0.043)
- Per-category accuracy:
  - E (emergency_now): 95.0% (19/20)
  - ...

## Inter-Rater Reliability
- Cardiology: Fleiss' kappa=0.823 (3 raters, 20 subjects)
- ...

## Cross-Level Analysis
- consultant: 89.2% agreement (κ=0.856, n=240)
- registrar: 85.1% agreement (κ=0.794, n=240)

## Disagreement Analysis
...
```

## Notes

- The script is designed to be robust to partial data and varying group sizes
- All comparisons require both specialist and gold labels to be present
- Critical disagreements (E↔S gaps) are flagged for manual review
- Kappa SEM (standard error of measurement) is provided per specialty for confidence intervals
