# Scored summary

- Rows: 60
- Cases (inferred): 30

## baseline

- score_safety: mean=0.900 (n=30)
- score_grounding: mean=1.633 (n=30)
- score_uncertainty: mean=1.767 (n=30)
- score_actionability: mean=1.467 (n=30)
- hard_fail rate: 0.367 (n=30)
- model_escalation counts: {'U': 12, 'R': 9, 'E': 8, 'S': 1}

## constrained

- score_safety: mean=1.433 (n=30)
- score_grounding: mean=1.567 (n=30)
- score_uncertainty: mean=1.633 (n=30)
- score_actionability: mean=1.567 (n=30)
- hard_fail rate: 0.267 (n=30)
- model_escalation counts: {'E': 20, 'U': 6, 'R': 4}

## Deltas (constrained - baseline)

- score_safety delta mean: 0.533 (n=30)
- score_grounding delta mean: -0.067 (n=30)
- score_uncertainty delta mean: -0.133 (n=30)
- score_actionability delta mean: 0.100 (n=30)
- hard_fail delta mean: -0.100 (n=30)

