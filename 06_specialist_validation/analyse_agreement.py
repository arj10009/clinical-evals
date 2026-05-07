#!/usr/bin/env python3
"""
Specialist Validation Agreement Analysis

Analyzes specialist triage decisions against gold standard labels and computes:
- Per-specialty agreement rates with author gold labels
- Cohen's kappa agreement statistics
- Per-category accuracy (E/U/R/S)
- Inter-rater reliability between specialists (Fleiss' kappa for 3+, Cohen's for 2)
- Cross-level analysis (consultant vs registrar)
- Ordinal distance analysis for disagreements
- Critical disagreement flagging

Outputs:
- specialist_responses_scored.csv: Original data with agreement column filled
- specialist_validation_report.md: Comprehensive markdown report
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd

# Try to import Cohen's kappa from sklearn, fall back to manual implementation
try:
    from sklearn.metrics import cohen_kappa_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available, will use manual Cohen's kappa implementation")


def cohen_kappa_manual(y1, y2):
    """
    Manual implementation of Cohen's kappa coefficient for 2 raters.

    Args:
        y1, y2: arrays of ratings (can be ordinal/numeric)

    Returns:
        kappa coefficient
    """
    if len(y1) != len(y2):
        raise ValueError("y1 and y2 must be same length")

    if len(y1) == 0:
        return np.nan

    # Convert to numeric if needed
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)

    # Observed agreement
    po = np.mean(y1 == y2)

    # Expected agreement
    # Get unique labels and their marginal frequencies
    labels = np.unique(np.concatenate([y1, y2]))
    n = len(y1)

    pe = 0.0
    for label in labels:
        p1 = np.mean(y1 == label)
        p2 = np.mean(y2 == label)
        pe += p1 * p2

    # Kappa
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0

    kappa = (po - pe) / (1.0 - pe)
    return kappa


def fleiss_kappa(ratings):
    """
    Fleiss' kappa for inter-rater reliability with 3+ raters.

    Args:
        ratings: list of lists, where each inner list is one subject's ratings
                 (one rating per rater, length = number of raters, possibly with np.nan for missing)

    Returns:
        kappa coefficient
    """
    ratings = np.asarray(ratings, dtype=object)

    if len(ratings) == 0:
        return np.nan

    # Clean data: extract valid ratings for each subject, remove subjects with <2 ratings
    cleaned_ratings = []
    for subject_ratings in ratings:
        valid = [r for r in subject_ratings if not (isinstance(r, float) and np.isnan(r))]
        if len(valid) >= 2:
            cleaned_ratings.append(valid)

    if not cleaned_ratings:
        return np.nan

    # Convert to category strings/values and build contingency table
    all_labels = set()
    for subject_ratings in cleaned_ratings:
        all_labels.update(subject_ratings)

    labels = sorted(list(all_labels))
    label_to_idx = {label: i for i, label in enumerate(labels)}

    n_subjects = len(cleaned_ratings)
    n_categories = len(labels)

    # Build contingency table: n_jk = count of label k by raters for subject j
    n_jk = np.zeros((n_subjects, n_categories))

    for j, subject_ratings in enumerate(cleaned_ratings):
        m_j = len(subject_ratings)  # number of raters for subject j
        for rating in subject_ratings:
            k = label_to_idx[rating]
            n_jk[j, k] += 1

    # Compute p_k (marginal proportion of category k)
    n_total = np.sum(n_jk)
    p_k = np.sum(n_jk, axis=0) / n_total

    # Observed agreement per subject
    po_j = np.zeros(n_subjects)
    for j in range(n_subjects):
        m_j = np.sum(n_jk[j, :])
        if m_j > 1:
            po_j[j] = (np.sum(n_jk[j, :] ** 2) - m_j) / (m_j * (m_j - 1))

    po = np.mean(po_j)

    # Expected agreement
    pe = np.sum(p_k ** 2)

    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0

    kappa = (po - pe) / (1.0 - pe)
    return kappa


def map_escalation_to_label(escalation_code):
    """Map E/U/R/S to full labels."""
    mapping = {
        'E': 'emergency_now',
        'U': 'urgent_same_day',
        'R': 'routine_visit',
        'S': 'self_care'
    }
    return mapping.get(escalation_code, None)


def ordinal_distance(label1, label2):
    """
    Compute ordinal distance between two labels.
    Order: emergency_now (0) > urgent_same_day (1) > routine_visit (2) > self_care (3)
    Returns: distance (0 if match, positive if different)
    """
    order = {
        'emergency_now': 0,
        'urgent_same_day': 1,
        'routine_visit': 2,
        'self_care': 3
    }
    if label1 not in order or label2 not in order:
        return np.nan
    return abs(order[label1] - order[label2])


def is_critical_disagreement(specialist_label, gold_label):
    """
    Flag critical disagreements: specialist says S but gold is E, or vice versa.
    These are maximum 3-step disagreements.
    """
    distance = ordinal_distance(specialist_label, gold_label)
    return distance == 3


def load_csv(filepath):
    """Load the specialist responses CSV."""
    print(f"Loading CSV from {filepath}...")
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} rows")
    return df


def compute_per_specialty_agreement(df):
    """
    Compute agreement metrics per specialty.

    Returns:
        dict with specialty -> {
            'raw_agreement': float,
            'kappa': float,
            'kappa_sem': float,
            'category_accuracy': dict,
            'n_comparisons': int,
            'specialists': list
        }
    """
    results = {}

    for specialty in df['specialty'].unique():
        if pd.isna(specialty):
            continue

        specialty_df = df[df['specialty'] == specialty].copy()

        # Filter to rows where both specialist and gold labels exist
        valid_mask = (
            specialty_df['specialist_escalation'].notna() &
            specialty_df['author_gold'].notna()
        )
        valid_df = specialty_df[valid_mask].copy()

        if len(valid_df) == 0:
            print(f"  {specialty}: No valid data")
            continue

        # Map escalation codes to labels
        valid_df['specialist_label'] = valid_df['specialist_escalation'].apply(map_escalation_to_label)
        valid_df['gold_label'] = valid_df['author_gold'].apply(map_escalation_to_label)

        # Compute raw agreement
        agreement_mask = valid_df['specialist_label'] == valid_df['gold_label']
        raw_agreement = agreement_mask.sum() / len(valid_df)

        # Compute Cohen's kappa
        specialist_labels = valid_df['specialist_label'].values
        gold_labels = valid_df['gold_label'].values

        if SKLEARN_AVAILABLE:
            kappa = cohen_kappa_score(gold_labels, specialist_labels)
        else:
            kappa = cohen_kappa_manual(gold_labels, specialist_labels)

        # Estimate SEM for kappa (simplified: sqrt(2(1-kappa)/(n*(1+kappa))))
        n = len(valid_df)
        if n > 0 and kappa < 1.0:
            kappa_sem = np.sqrt(2 * (1 - kappa) / (n * (1 + kappa)))
        else:
            kappa_sem = np.nan

        # Per-category accuracy (confusion matrix style)
        category_accuracy = {}
        for code in ['E', 'U', 'R', 'S']:
            label = map_escalation_to_label(code)
            mask = valid_df['gold_label'] == label
            if mask.sum() > 0:
                correct = (valid_df.loc[mask, 'specialist_label'] == label).sum()
                category_accuracy[code] = {
                    'correct': correct,
                    'total': mask.sum(),
                    'accuracy': correct / mask.sum()
                }

        # Get list of specialists
        specialists = valid_df['specialist_id'].unique().tolist()

        results[specialty] = {
            'raw_agreement': raw_agreement,
            'kappa': kappa,
            'kappa_sem': kappa_sem,
            'category_accuracy': category_accuracy,
            'n_comparisons': len(valid_df),
            'specialists': specialists
        }

        print(f"  {specialty}: {len(valid_df)} comparisons, {raw_agreement:.1%} raw agreement, kappa={kappa:.3f}")

    return results


def compute_inter_rater_reliability(df):
    """
    Compute inter-rater reliability within each specialty.
    For 2 specialists: Cohen's kappa
    For 3+ specialists: Fleiss' kappa

    Returns:
        dict with specialty -> {
            'n_raters': int,
            'kappa_type': str,
            'kappa': float,
            'n_subjects': int
        }
    """
    results = {}

    for specialty in df['specialty'].unique():
        if pd.isna(specialty):
            continue

        specialty_df = df[df['specialty'] == specialty].copy()

        # Map escalation to labels
        specialty_df['specialist_label'] = specialty_df['specialist_escalation'].apply(map_escalation_to_label)

        # Group by (case_id, turn) to get all specialists' ratings for each case
        grouped = specialty_df.groupby(['case_id', 'turn'])['specialist_label'].apply(list).reset_index()

        # Filter to items with at least 2 ratings
        grouped = grouped[grouped['specialist_label'].apply(len) >= 2].copy()

        if len(grouped) == 0:
            print(f"  {specialty}: No cases with 2+ specialists")
            continue

        # Determine number of raters (assume consistent across items)
        n_raters = max(grouped['specialist_label'].apply(len))

        if n_raters == 2:
            # Cohen's kappa: flatten to pairwise comparisons
            kappas = []
            for ratings in grouped['specialist_label'].values:
                if len(ratings) == 2:
                    k = cohen_kappa_manual([ratings[0]], [ratings[1]])
                    if not np.isnan(k):
                        kappas.append(k)

            if kappas:
                overall_kappa = np.mean(kappas)
            else:
                overall_kappa = np.nan

            results[specialty] = {
                'n_raters': 2,
                'kappa_type': "Cohen's kappa",
                'kappa': overall_kappa,
                'n_subjects': len(grouped)
            }
            print(f"  {specialty}: 2 raters, Cohen's kappa={overall_kappa:.3f} over {len(grouped)} cases")

        elif n_raters >= 3:
            # Fleiss' kappa
            ratings_list = grouped['specialist_label'].tolist()
            fk = fleiss_kappa(ratings_list)

            results[specialty] = {
                'n_raters': n_raters,
                'kappa_type': "Fleiss' kappa",
                'kappa': fk,
                'n_subjects': len(grouped)
            }
            print(f"  {specialty}: {n_raters} raters, Fleiss' kappa={fk:.3f} over {len(grouped)} cases")

    return results


def compute_level_agreement(df):
    """
    Compute agreement separately for consultant vs registrar.

    Returns:
        dict with level (consultant/registrar) -> {
            'raw_agreement': float,
            'kappa': float,
            'n_comparisons': int
        }
    """
    results = {}

    for level_col in ['grade']:  # Assume 'grade' has consultant/registrar
        for level_val in df[level_col].unique():
            if pd.isna(level_val):
                continue

            level_df = df[df[level_col] == level_val].copy()

            # Filter to valid rows
            valid_mask = (
                level_df['specialist_escalation'].notna() &
                level_df['author_gold'].notna()
            )
            valid_df = level_df[valid_mask].copy()

            if len(valid_df) == 0:
                continue

            # Map labels
            valid_df['specialist_label'] = valid_df['specialist_escalation'].apply(map_escalation_to_label)
            valid_df['gold_label'] = valid_df['author_gold'].apply(map_escalation_to_label)

            # Compute metrics
            agreement_mask = valid_df['specialist_label'] == valid_df['gold_label']
            raw_agreement = agreement_mask.sum() / len(valid_df)

            if SKLEARN_AVAILABLE:
                kappa = cohen_kappa_score(valid_df['gold_label'].values, valid_df['specialist_label'].values)
            else:
                kappa = cohen_kappa_manual(valid_df['gold_label'].values, valid_df['specialist_label'].values)

            results[level_val] = {
                'raw_agreement': raw_agreement,
                'kappa': kappa,
                'n_comparisons': len(valid_df)
            }

            print(f"  {level_val}: {len(valid_df)} comparisons, {raw_agreement:.1%} agreement, kappa={kappa:.3f}")

    return results


def compute_disagreements(df):
    """
    Analyze disagreements: type (ordinal distance) and flag critical.

    Returns:
        DataFrame with disagreement details
    """
    # Filter to valid rows
    valid_mask = (
        df['specialist_escalation'].notna() &
        df['author_gold'].notna()
    )
    disagreement_rows = []

    for idx, row in df[valid_mask].iterrows():
        specialist_label = map_escalation_to_label(row['specialist_escalation'])
        gold_label = map_escalation_to_label(row['author_gold'])

        if specialist_label != gold_label:
            distance = ordinal_distance(specialist_label, gold_label)
            is_critical = is_critical_disagreement(specialist_label, gold_label)

            disagreement_rows.append({
                'specialist_id': row['specialist_id'],
                'specialty': row['specialty'],
                'grade': row['grade'],
                'case_id': row['case_id'],
                'turn': row['turn'],
                'specialist_label': specialist_label,
                'gold_label': gold_label,
                'ordinal_distance': distance,
                'is_critical': is_critical
            })

    return pd.DataFrame(disagreement_rows)


def fill_agreement_column(df):
    """Fill the 'agreement' column with 'match' or 'mismatch'."""
    df = df.copy()

    def check_agreement(row):
        if pd.isna(row['specialist_escalation']) or pd.isna(row['author_gold']):
            return np.nan

        specialist_label = map_escalation_to_label(row['specialist_escalation'])
        gold_label = map_escalation_to_label(row['author_gold'])

        return 'match' if specialist_label == gold_label else 'mismatch'

    df['agreement'] = df.apply(check_agreement, axis=1)
    return df


def generate_report(df, specialty_results, inter_rater_results, level_results, disagreements):
    """Generate markdown report."""
    report_lines = []

    report_lines.append("# Specialist Validation Agreement Report\n")

    report_lines.append("## Summary\n")
    total_comparisons = sum(r.get('n_comparisons', 0) for r in specialty_results.values())
    total_specialists = len(df['specialist_id'].dropna().unique())
    total_specialties = len(specialty_results)

    report_lines.append(f"- **Total specialists**: {total_specialists}\n")
    report_lines.append(f"- **Total specialties**: {total_specialties}\n")
    report_lines.append(f"- **Total specialist-gold comparisons**: {total_comparisons}\n")
    report_lines.append(f"- **Total disagreements**: {len(disagreements)}\n")
    critical_count = disagreements['is_critical'].sum() if len(disagreements) > 0 and 'is_critical' in disagreements.columns else 0
    report_lines.append(f"- **Critical disagreements** (E\u2194S): {critical_count}\n")

    report_lines.append("\n## Per-Specialty Agreement\n")

    for specialty, results in sorted(specialty_results.items()):
        report_lines.append(f"\n### {specialty}\n")
        report_lines.append(f"- **Specialists**: {', '.join(map(str, results['specialists']))}\n")
        report_lines.append(f"- **Comparisons**: {results['n_comparisons']}\n")
        report_lines.append(f"- **Raw agreement**: {results['raw_agreement']:.1%}\n")
        report_lines.append(f"- **Cohen's kappa**: {results['kappa']:.3f} (±{results['kappa_sem']:.3f})\n")

        report_lines.append("- **Per-category accuracy**:\n")
        for code in ['E', 'U', 'R', 'S']:
            label = map_escalation_to_label(code)
            if code in results['category_accuracy']:
                acc = results['category_accuracy'][code]
                report_lines.append(
                    f"  - {code} ({label}): {acc['accuracy']:.1%} ({acc['correct']}/{acc['total']})\n"
                )

    report_lines.append("\n## Inter-Rater Reliability\n")

    if inter_rater_results:
        for specialty, results in sorted(inter_rater_results.items()):
            kappa_type = results['kappa_type']
            kappa = results['kappa']
            n_raters = results['n_raters']
            n_subj = results['n_subjects']

            report_lines.append(
                f"- **{specialty}**: {kappa_type}={kappa:.3f} "
                f"({n_raters} raters, {n_subj} subjects)\n"
            )
    else:
        report_lines.append("- No cases with 2+ specialists per specialty\n")

    report_lines.append("\n## Cross-Level Analysis\n")

    for level, results in sorted(level_results.items()):
        report_lines.append(
            f"- **{level}**: {results['raw_agreement']:.1%} agreement "
            f"(κ={results['kappa']:.3f}, n={results['n_comparisons']})\n"
        )

    report_lines.append("\n## Disagreement Analysis\n")

    if len(disagreements) > 0:
        # Summarize by ordinal distance
        report_lines.append("\n### By Ordinal Distance\n")
        for distance in sorted(disagreements['ordinal_distance'].unique()):
            mask = disagreements['ordinal_distance'] == distance
            count = mask.sum()
            label_map = {1: "1-step", 2: "2-step", 3: "3-step"}
            report_lines.append(f"- **{label_map.get(distance, 'unknown')}-distance**: {count}\n")

        # Critical disagreements
        report_lines.append("\n### Critical Disagreements (3-step, E↔S)\n")
        critical = disagreements[disagreements['is_critical']]
        if len(critical) > 0:
            report_lines.append(f"- **Count**: {len(critical)}\n")
            report_lines.append("- **Details**:\n")
            for idx, row in critical.iterrows():
                report_lines.append(
                    f"  - {row['specialist_id']} ({row['specialty']}, {row['grade']}): "
                    f"case {row['case_id']}, turn {row['turn']}: "
                    f"{row['specialist_label']} vs gold {row['gold_label']}\n"
                )
        else:
            report_lines.append("- None\n")
    else:
        report_lines.append("- No disagreements\n")

    report_lines.append("\n---\n")
    report_lines.append("*Report generated by analyse_agreement.py*\n")

    return "".join(report_lines)


def main():
    """Main analysis pipeline."""
    print("=" * 70)
    print("Specialist Validation Agreement Analysis")
    print("=" * 70)

    # Determine script location and file paths
    script_dir = Path(__file__).parent
    csv_path = script_dir / "specialist_responses.csv"
    output_csv_path = script_dir / "specialist_responses_scored.csv"
    report_path = script_dir / "specialist_validation_report.md"

    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found")
        sys.exit(1)

    # Load data
    df = load_csv(csv_path)

    print("\n" + "=" * 70)
    print("Per-Specialty Agreement Analysis")
    print("=" * 70)
    specialty_results = compute_per_specialty_agreement(df)

    print("\n" + "=" * 70)
    print("Inter-Rater Reliability Analysis")
    print("=" * 70)
    inter_rater_results = compute_inter_rater_reliability(df)

    print("\n" + "=" * 70)
    print("Cross-Level Analysis")
    print("=" * 70)
    level_results = compute_level_agreement(df)

    print("\n" + "=" * 70)
    print("Disagreement Analysis")
    print("=" * 70)
    disagreements = compute_disagreements(df)
    print(f"Total disagreements: {len(disagreements)}")
    if len(disagreements) > 0:
        critical_count = disagreements['is_critical'].sum()
        print(f"Critical disagreements (3-step): {critical_count}")

    print("\n" + "=" * 70)
    print("Generating Report and Saving Results")
    print("=" * 70)

    # Generate report
    report = generate_report(df, specialty_results, inter_rater_results, level_results, disagreements)
    report_path.write_text(report)
    print(f"Report saved to {report_path}")

    # Fill agreement column and save
    df_scored = fill_agreement_column(df)
    df_scored.to_csv(output_csv_path, index=False)
    print(f"Scored CSV saved to {output_csv_path}")

    print("\n" + "=" * 70)
    print("Analysis Complete")
    print("=" * 70)


if __name__ == '__main__':
    main()
