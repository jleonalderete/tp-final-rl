# Experiment log

Chronological record of runs. It's the source for the report's Development section and
diagnostic case study: every result that appears in the report needs an entry here.

- One entry per run or sweep that teaches something, failed ones included. New entries go at
  the end.
- The entry title is the run's directory name under `runs/`.
- Run from a clean commit and record its short hash, so the run can be reproduced and cited in
  the report.

Template:

```markdown
### YYYY-MM-DD_<description>

- **Author:**
- **Commit:**
- **Goal:** the question the run answers or the hypothesis it tests.
- **Configuration:** algorithm, hyperparameters, environment parameters, seeds.
- **Result:** concrete metrics and paths to figures.
- **Conclusion:** what we learned and the next step.
```

## Runs
