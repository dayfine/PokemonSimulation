# PLZA opening: story-event review draft

Read [the JSON](examples/plza-opening.draft.json) alongside this page: **39 events,
four checkpoints**, ending after Main Mission 03. Totodile is an explicit example
choice. This is a guide-authored plan proposal, not a native table export, recorded
run, executable route or battle simulation. The intro is our grouping, not an
official numbered mission. Public sources were checked on 2026-11-06; the game
revision is still an input, and guides are not pinned game data.

## Walkthrough of the proposed events

| Checkpoint | Ordered actions | Required confirmation |
|---|---|---|
| Intro (5) | Supply setup choices → station arrival → ticket gate exit → meet companion → city introduction / bag theft | Mission 01 active; companion branch identified |
| 01 — Get Your Travel Bag Back! (4) | Follow starters → choose Totodile → battle Andi → bag/partner scene | Required battle won; bag returned; mission complete |
| 02 — Escape from the Battle Zone! (10) | Night activation → follow companion → battle Brigitte → Floette rescue → enter Hotel Z → AZ check-in → lift to 2F → room 202 → bed → visitor / roof scene | Required battle won; interior and room arrivals confirmed; mission complete |
| 03 — A New Life in Lumiose City (20) | Lobby / Team MZ → movement tutorial → companion battle → rooftop detour to Center → Pokédex → Wild Zone 1 → capture tutorials → species gate → lab / Mable / research reward → leave lab → teach Rock Smash → clear passage → return / report | Tutorial battle result recorded; species count checked; TM received and move learned; passage observed open; mission complete |

Intro and Mission 01 follow [the opening walkthrough](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Legends:_Z-A/Part_1).
Mission 02 follows [the night/Hotel Z walkthrough at revision 4404991](https://bulbapedia.bulbagarden.net/w/index.php?title=Walkthrough:Pok%C3%A9mon_Legends:_Z-A/Part_2&oldid=4404991).
Mission numbering and completion objectives follow [the mission list](https://pokemondb.net/legends-z-a/missions).
Every JSON event names its source references; most guide pages are mutable.

## Battle and collection details that matter

| Event | Guide-derived opponent, for this Totodile example | Progression rule |
|---|---|---|
| `01/andi` | Pancham Lv. 4 | Win required |
| `02/brigitte` | Cleffa Lv. 4, Bunnelby Lv. 4 | Win required |
| `03/companion_training` | Tepig Lv. 5, then Chikorita Lv. 5 | Win or loss can continue; confirm the following story state |

The first two teams come from the opening/night sources above. The companion
team and its loss-tolerant progression come from [the morning walkthrough](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Legends:_Z-A/Part_3).
A loss that advances the tutorial remains a **battle loss** in the history. Floette's
rescue is a scene, not three additional simulated trainer wins.

Mission 03 needs **five registered species**; it does not mean five successful
throws or five duplicate catches. The plan includes Fletchling and Bunnelby,
then reads the current Pokédex and targets missing species. Capture mechanics
and the Bunnelby tutorial need a PLZA-specific profile. Keep Bunnelby available
for Rock Smash. See [the capture/return walkthrough](https://www.thonky.com/pokemon-legends-z-a/main-mission-03-a-new-life-in-lumiose-city).

The first “Filling Your Pokédex” research stage has a five-species objective;
TM004 Rock Smash is the **research level 2 reward**. These are separate observed
gates: request completion, reward claimability, receipt, then move knowledge.
The draft must not infer ownership just from reaching the species count.
See [research requests and rewards](https://pokemondb.net/legends-z-a/research).
The lab destination and return via Rock Smash also follow [the mission walkthrough](https://gmtreks.com/pokemon-z-a/main-missions/4).

## What is shared, and what is PLZA-specific?

The [common draft](STORY_PLAN_DRAFT.md) supplies ordered checkpoints/events,
requirements, expectations, data identities and outcomes. PLZA adds versioned
profiles in `action.game`: landmark routing, real-time trainer battles, capture
tutorials, research rewards, elevators and field moves. The JSON stays separate
from their eventual typed native/Python implementations.

The example deliberately exercises more than FRLG/BDSP tile walking:

- A landmark is a semantic destination, **not a coordinate**. The rooftop drop is
  one-way; a reverse route cannot be assumed. Hotel/lab arrivals need evidence.
- A companion role is bound from the avatar branch, not a hardcoded NPC name.
- “Register until five species” is a bounded objective with encounter selection,
  not a fixed list of two extra button sequences. Its catalog is unbound.
- Research, teaching and field use are distinct actions with prerequisites.
- PLZA has real-time movement and attacks; the [official battle description](https://legends.pokemon.com/en-us/gameplay)
  requires a separate rules/executor adapter. There are no Gen 3 win rates here.

## How to interpret the JSON

All map/ruleset/encounter/executor/observation bindings are **unbound**. Every
action inherits the top-level requirements and `execution_policy`, then adds its
own requirements. `expected` records a guide-derived claim or progression target;
it is never an observation or permission to update actual state. A battle action
records the actual result and separately checks its `story_gate`.

Profiles, predicates and landmark names are proposals local to this example,
not a registered schema/API. `via` lists describe intended traversal; they are
not controller instructions. We have no verified map, tile/3D frame, path costs,
scene detector, exact input timings, initial party stats/HP or bag ledger. Setup
choices and game revision are required run inputs. Rest and Center scenes do not
silently establish full HP. Move replacement is unresolved pending a menu read.

The numeric retry/capture limits are **author policy proposals**, not mechanics
or native defaults. Every retry needs a confirmed state and a safe adapter rule.
Timeouts still need binding. Unsupported actions, ambiguous location or exhausted
budgets stop explicitly. Interruptions invalidate pose and pending effects before
re-observation; an already-consumed scene requires evidence before skipping it.
No automatic new-game/reset, save manipulation or live execution is implemented.

## Next binding work

1. Review this sequence and the FRLG/BDSP examples together before stabilizing
   the envelope/profile catalog. PLZA should expose missing concepts early.
2. Bind a specific game revision and observed checkpoint states. Supply maps,
   landmark/scene observations, party/bag and real-time battle/capture data.
3. Export/replay native actions and observations, then compare those traces with
   Python. Until then, format/reference checks establish document consistency
   only; they do not establish game feasibility or end-to-end success.
