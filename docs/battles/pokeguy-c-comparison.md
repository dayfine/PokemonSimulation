# Type C strategy comparison

Only the 12 opted-in C fights were rerun. The other 57 retain their published baseline point estimates. That retained cohort is historical-policy data, not a new probability measurement of the refactored B controller.

The fresh validation uses seed 4 and 5,520 trials. The original 69-fight table remains unchanged. The NPC model and recorded player inputs are unchanged.

## Old and new C estimates

Changes are percentage points. “Unresolved” means the simultaneous change interval includes zero; a larger point estimate alone does not establish improvement.

| Fight | Baseline | New C | Change | New trials | Evidence |
|---|---:|---:|---:|---:|---|
| tower-rival | 98.3% | 90.0% | -8.3 pp | 700 | unresolved |
| koga | 41.6% | 70.1% | +28.4 pp | 1700 | improved |
| erika | 94.4% | 91.5% | -2.9 pp | 620 | unresolved |
| silph-rival | 90.3% | 96.3% | +6.1 pp | 300 | unresolved |
| silph-giovanni | 91.1% | 100.0% | +8.9 pp | 100 | unresolved |
| sabrina | 98.3% | 98.3% | +0.0 pp | 180 | unresolved |
| route22-rival | 36.4% | 95.6% | +59.2 pp | 340 | improved |
| lorelei | 96.6% | 94.3% | -2.2 pp | 440 | unresolved |
| bruno | 30.6% | 95.9% | +65.3 pp | 320 | improved |
| agatha | 95.0% | 95.3% | +0.3 pp | 360 | unresolved |
| lance | 76.9% | 99.2% | +22.3 pp | 120 | improved |
| champion | 56.1% | 95.6% | +39.5 pp | 340 | improved |

## New top ten by point estimate

| Rank | Fight | Win rate | Simultaneous interval | Tier | Data |
|---:|---|---:|---:|---|---|
| 1 | cerulean-rival | 41.7% | 36.6%–46.9% | B | retained baseline |
| 2 | ssanne-rival | 48.7% | 43.5%–53.8% | B | retained baseline |
| 3 | brock | 52.0% | 46.9%–57.2% | A | retained baseline |
| 4 | surge | 57.4% | 52.2%–62.5% | B | retained baseline |
| 5 | pewter-liam | 66.6% | 61.3%–71.6% | A | retained baseline |
| 6 | koga | 70.1% | 64.9%–74.9% | C | fresh C trials |
| 7 | mtmoon-josh | 84.7% | 79.1%–89.4% | B | retained baseline |
| 8 | forest-sammy | 88.8% | 83.0%–93.2% | B | retained baseline |
| 9 | tower-rival | 90.0% | 84.3%–94.3% | C | fresh C trials |
| 10 | erika | 91.5% | 85.7%–95.5% | C | fresh C trials |

## Interpretation and reproduction

The combined intervals and change intervals have at least 95% simultaneous coverage under the model. Half the error budget covers all original cases before retaining any subset; half covers the fresh C trials. Retained bounds were widened slightly without rerunning those fights. Only the fresh C intervals are sampled to the new 10-percentage-point width target.

These are conditional solo-lead estimates, not cartridge measurements or a route completion probability. The original NPC replacement approximation remains, including possible departures from the video’s enemy order. Player switching is not implemented.

```sh
PYTHONPATH=src python3 -m pokesim.cli.frlg_run_battles --complex-only --seed 4 --out /tmp/pokeguy-c.json
```

The [machine-readable comparison](pokeguy-c-comparison.json) records bounds, goals, item use, seeds and provenance. See [strategy layers](player-strategies.md) and the [historical baseline](pokeguy-trainers.md).
