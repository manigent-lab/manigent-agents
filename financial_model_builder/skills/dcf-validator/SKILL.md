---
name: dcf-validator
description: Validate a DCF workbook or a JSON of DCF inputs - terminal growth vs WACC and vs the riskfree rate, WACC plausibility, rates stored as whole numbers, PV of terminal value as a share of EV, discount periods vs the mid-year switch (stubs included), and the exponent actually used to discount the terminal value (end of year N vs N - 0.5, exit-multiple TV discounted mid-year), plus error values and uncalculated formulas. Use after building or before reviewing any DCF.
---

<!-- The check list follows scripts/validate_dcf.py of the dcf-model skill in
     anthropics/financial-services (Apache-2.0, Copyright Anthropic, PBC) at commit
     574ed3624aebd0418c7e96cd101262f30210ab26. No code was copied: dcf_validator.py was
     written for this pool by Manigent Contributors (2026-10-11) and adds the
     riskfree ceiling, mid-year / stub detection and terminal-value timing checks. -->

# dcf-validator

```bash
H="$MANIGENT_AGENT_DIR/personal-skill-hub/skills/dcf-validator/dcf_validator.py"
python3 $H --xlsx model.xlsx --format table [--sheet DCF --sheet WACC] [--riskfree <decimal>] [--tv-method gordon|exit]
python3 $H --json inputs.json --format table
```

- The workbook must be **recalculated** (cached values); the script reports
  `not_calculated` otherwise.
- Inputs are found by row label, first number to the right. Labels it understands:
  WACC / discount rate, terminal or perpetuity growth, risk-free / 10-year Treasury,
  terminal value, PV of terminal value, enterprise value, exit multiple, mid-year
  (Yes/No/1/0), discount period (a row of periods). `inputs_not_found` lists what it
  could not locate; use `--json` with those keys when labels are unusual.
- Pass `--riskfree` with the dated observation you used (e.g. from
  `knowledge/treasury-par-yield-curve-2026.csv`) if the workbook has no riskfree row.
- `--tv-method` defaults to gordon when a growth rate is present, exit otherwise.

Reading the result:
- `tv_timing` reports the exponent implied by TV, PV(TV) and WACC and whether it equals
  N or N - 0.5. An exit-multiple TV at N - 0.5 is a finding; a Gordon TV at either is a
  convention the answer must state (see `memory/learnings/dcf-conventions.md`).
- `discount_convention` notes when a schedule is ambiguous (a full-year mid-year schedule
  and an end-year schedule after a half-year stub look the same); the mid-year switch
  decides.
- The WACC band and TV-share threshold are review prompts, not errors.

Report the findings table, then the conventions the model uses (discount timing, TV
method and timing, share-count method) in one line each.
