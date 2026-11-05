# League PP requirements: separate from pickup routing

Blizzard has 5 base PP. The recorded run uses 5 casts against Lance and 2
against Champion: 7 total. Surf uses 16 casts across the five fights, exceeding
its base 15. No PP Ups are assumed.

| Fight | Recorded Surf casts | Recorded Blizzard casts | Assumed entry Surf PP | Assumed entry Blizzard PP |
|---|---:|---:|---:|---:|
| Lorelei | 1 | 0 | 15 | 5 |
| Bruno | 5 | 0 | 14 | 5 |
| Agatha | 5 | 0 | 9 | 5 |
| Lance | 1 | 5 | 4 | 5 |
| Champion | 4 | 2 | 13 | 5 |

The recorded solution is **one Elixir after Lance and before Champion**:
Surf 3 → 13, Blizzard 0 → 5, and Bite 18 → 25. Elixir restores up to 10 PP
to each move, capped at that move's maximum. One Max Elixir, or two
single-move Ether/Max Ether recoveries targeting Surf and Blizzard, can provide
at least that recovery capability. These alternatives are not separately
benchmarked battle inputs.

The combat/resource layer should export the following requirements:

- Enter the League with the assumed full PP: Bite25, Surf15, Blizzard5, Strength15.
- Preserve the ability to enter Lance with Blizzard5 and the Champion with Blizzard5.
- Reserve recovery capacity for both Surf and Blizzard in the Lance-to-Champion window;
  one Elixir is the recorded solution.
- Do not spend that reserved item earlier without replacing its recovery capacity.
- Determine an additional stochastic reserve from actual move/PP consumption
  before claiming the plan is reliable across the whole League.

The machine-readable contract is
[`league-pp-requirements.json`](../../data/runs/pokeguy-leafgreen-15934/league-pp-requirements.json).
It lists the entry assumptions, recorded consumption and required recovery
capability. A **separate logistics process** can resolve where/when to pick up,
buy, reserve and use the supplies. This change does not plan those acquisitions.

The new C benchmark still resets each fight to its recorded PP and inventory.
Its example traces can spend more moves than the video; misses also consume PP.
None of the independently sampled League fights used an in-battle PP item,
but that does not establish sufficiency for a chained League run. In particular,
those trials assume the recorded pre-Champion Elixir has already restored PP.
The seven-cast observed Blizzard budget is a baseline, not a validated worst-case
or high-probability budget for C.
