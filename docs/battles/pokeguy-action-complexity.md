# Pokeguy: battle risk and player-action complexity

This classifies the existing 69-trainer benchmark, using the recorded entry states and `solo-setup-heal/4` policy. No new simulations or alternate-team analyses were run.

Win probability measures risk under this policy. Action complexity measures which kinds of decisions our controller makes. A dangerous fight can still need only a simple attack policy.

## Ten lowest baseline win rates

Intervals have 95% simultaneous coverage across all 69 cases and sampling looks, conditional on the model. Overlapping intervals mean close ranks are not established differences; Koga and the Cerulean rival are effectively tied here.

| Rank | Fight | Win rate | Simultaneous interval | Action tier |
|---:|---|---:|---:|---|
| 1 | Bruno | 30.6% | 25.8%–35.8% | C |
| 2 | Route 22 rival | 36.4% | 31.5%–41.5% | C |
| 3 | Koga | 41.6% | 36.7%–46.7% | C |
| 4 | Cerulean rival | 41.7% | 36.8%–46.7% | B |
| 5 | S.S. Anne rival | 48.7% | 43.7%–53.7% | B |
| 6 | Brock | 52.0% | 47.0%–57.0% | A |
| 7 | Champion | 56.1% | 51.1%–61.1% | C |
| 8 | Lt. Surge | 57.4% | 52.4%–62.4% | B |
| 9 | Pewter Camper Liam | 66.6% | 61.5%–71.5% | A |
| 10 | Lance | 76.9% | 71.7%–81.6% | C |

## Grouping rule and interpretation

Assign the highest action tier observed in the baseline trials: any setup-item use gives C; otherwise any recovery-item use gives B; otherwise A. Even rare item use counts. Means include both wins and losses. These are observed policy behaviors, **not proven minimum policies**: an item being used does not establish that it improved the win rate or was needed.

| Tier | Fights | Our side needs to represent | Examples |
|---|---:|---|---|
| A — attacks | 34 | Repeated attacks or effective-move selection, PP limits and move locks | Brock, Liam, most Route 3/Nugget Bridge trainers, Viridian gym Giovanni |
| B — recovery | 23 | Attack/heal/cure decisions; potion size, incoming damage, residual damage, status and PP medicine | Misty, Cerulean rival, S.S. Anne rival, Surge, Blaine |
| C — setup | 12 | Recovery plus setup timing, stages, speed thresholds, accuracy, PP and benefits across the remaining opposing team | Tower rival, Koga, Erika, Silph fights and the League |

Tier A does not imply a safe battle: Liam starts at Lv8 with 5/27 HP, and Brock at Lv11 with 11/33 HP. Neither has HP recovery in the recorded entry bag. Their low rates point toward preparation/entry-state changes rather than a sophisticated in-battle item policy. The example Brock win uses Bubble throughout.

Tier B is about timing, not just checking whether HP is below half. Cerulean and S.S. Anne rivals combine Leech Seed, sleep, poison and damaging attacks; spending a turn healing or curing can change the outcome. Surge adds paralysis and Raichu’s damage/evasion pressure.

Tier C needs planning beyond the current opponent. Bruno’s losses overwhelmingly end against Machamp; early setup must pay off later. Route 22 and Champion combine different type matchups, speed thresholds and limited move PP. Koga and Champion also expose accuracy loss during setup. The present heuristic does not choose Guard Spec despite engine support, so these rates should not be interpreted as an optimized setup strategy.

Switching would be a further extension of C: it could clear Leech Seed/stat drops or bring in a supporter, but its costs, incoming hits and resulting matchup must be modeled. **No battle has been demonstrated to require a switch.** The current solo-lead benchmark does not evaluate deliberate player switching and omits pre-Plateau HM helpers for Roar/Whirlwind. Supporter/switch strategies therefore cannot be ranked from these results.

To establish the minimum useful controller, compare matched attack-only, recovery-enabled and setup-enabled policies against a chosen reliability target. Those comparisons have not been run for this classification.

## Complete grouping

### A — Attack selection (34 fights)

- `lab-rival`
- `pewter-liam`
- `brock`
- `route3-colton`
- `route3-greg`
- `route3-james`
- `mtmoon-rocket`
- `bridge-cale`
- `bridge-timmy`
- `bridge-reli`
- `bridge-ethan`
- `bridge-rocket`
- `route25-wayne`
- `route25-kelsey`
- `route25-flint`
- `route6-jeff`
- `vermilion-tucker`
- `rocktunnel-allen`
- `rocktunnel-oliver`
- `rocktunnel-dudley`
- `route8-rich`
- `hideout-key-grunt`
- `hideout-left-guard`
- `tower-tammy`
- `tower-jennifer`
- `tower-emilia`
- `tower-rocket1`
- `tower-rocket2`
- `tower-rocket3`
- `fuchsia-kirk`
- `celadon-tamia`
- `celadon-lori`
- `viridian-warren`
- `giovanni-gym`

### B — Recovery decisions (23 fights)

- `forest-sammy`
- `mtmoon-josh`
- `mtmoon-miguel`
- `misty`
- `cerulean-rival`
- `bridge-ali`
- `route25-haley`
- `cerulean-dig-rocket`
- `ssanne-rival`
- `surge`
- `route9-alicia`
- `route9-conner`
- `rocktunnel-ashton`
- `rocktunnel-winston`
- `rocktunnel-martha`
- `rocktunnel-sofia`
- `rocktunnel-dana`
- `hideout-poster-guard`
- `hideout-right-guard`
- `hideout-giovanni`
- `blaine`
- `silph-boardroom-grunt`
- `viridian-takashi`

### C — Setup planning (12 fights)

- `tower-rival`
- `koga`
- `erika`
- `silph-rival`
- `silph-giovanni`
- `sabrina`
- `route22-rival`
- `lorelei`
- `bruno`
- `agatha`
- `lance`
- `champion`

See the [full results](pokeguy-trainers.md), [machine-readable evidence](pokeguy-trainers.json), [benchmark definition](pokeguy-benchmark.md), and [remaining model gaps](GAPS.md).
