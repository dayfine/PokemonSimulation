# Pokeguy's Squirtle-line move history

Recorded-run reconstruction from the video notes and pinned pret level-up learnsets.

Moves below are **membership lists, not controller slot order or PP**. Video times are playback ranges from sampled review; they are not exact button-edge timestamps. The two slot-reorder windows described below remain unresolved.

Disable and exhausted PP do not remove a known move; this report tracks learned moves, not turn-by-turn legal actions.

This follows the observed wild wins and Rare Candies. It does not apply the recorded learning times to the flee-all counterfactual.

## Learning and replacement points

Initial Lv5 Squirtle: Tackle, Tail Whip.

| Video range | Anchor | Decision | Moves afterward |
|---|---|---|---|
| [0:04:15–0:04:22](https://www.youtube.com/watch?v=CbfjWuRWH10&t=255) | route1-pidgey-defeated / after_foe 1 | learn Bubble (level_up, Lv7) | Tackle, Tail Whip, Bubble |
| [0:11:55–0:12:08](https://www.youtube.com/watch?v=CbfjWuRWH10&t=715) | pewter-liam / after_foe 2 | learn Withdraw (level_up, Lv10) | Tackle, Tail Whip, Bubble, Withdraw |
| [0:12:55–0:13:12](https://www.youtube.com/watch?v=CbfjWuRWH10&t=775) | brock / after_foe 2 | learn Water Gun over Tail Whip (level_up, Lv13) | Tackle, Water Gun, Bubble, Withdraw |
| [0:22:07–0:22:25](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1327) | cerulean-candy1 / before | learn Mega Kick over Withdraw (tutor) | Tackle, Water Gun, Bubble, Mega Kick |
| [0:23:01–0:23:14](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1381) | cerulean-candy1 / after | learn Bite over Bubble (level_up, Lv19) | Tackle, Water Gun, Bite, Mega Kick |
| [0:24:43–0:24:56](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1483) | cerulean-rival / before | learn Water Pulse over Tackle (TM03) | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:33:19–0:33:25](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1999) | route25-haley / after_foe 1 | decline Rapid Spin (level_up, Lv25) | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:50:21–0:51:23](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3021) | rocktunnel-oliver / after_foe 2 | decline Protect (level_up, Lv31) | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:14:55–1:15:13](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4495) | fuchsia-kirk / before | learn Surf over Water Gun (HM03) | Water Pulse, Surf, Bite, Mega Kick |
| [1:24:30–1:24:59](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5070) | celadon-tamia / after_foe 2 | decline Rain Dance (level_up, Lv42) | Water Pulse, Surf, Bite, Mega Kick |
| [1:25:00–1:25:29](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5100) | celadon-lori / before | learn Blizzard over Mega Kick (TM14) | Water Pulse, Surf, Bite, Blizzard |
| [1:43:24–1:43:41](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6204) | lorelei / before | learn Strength over Water Pulse (HM04) | Strength, Surf, Bite, Blizzard |
| [1:54:43–1:54:50](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6883) | lance / after_foe 3 | decline Skull Bash (level_up, Lv55) | Strength, Surf, Bite, Blizzard |

## Move set for every battle

Changes after a knockout apply only to subsequent opponents. For example, Brock is fought with Bubble and learns Water Gun after Onix; Misty is fought without Water Pulse. JSON output also records the lead's move set before and after every defeated opponent.

| Video start | Battle | Level before | Moves on entry | Moves on exit |
|---|---|---:|---|---|
| [0:01:57](https://www.youtube.com/watch?v=CbfjWuRWH10&t=117) | lab-rival | 5 | Tackle, Tail Whip | Tackle, Tail Whip |
| [0:03:10](https://www.youtube.com/watch?v=CbfjWuRWH10&t=190) | route1-rattata-defeated | 6 | Tackle, Tail Whip | Tackle, Tail Whip |
| [0:03:54](https://www.youtube.com/watch?v=CbfjWuRWH10&t=234) | route1-pidgey-defeated | 6 | Tackle, Tail Whip | Tackle, Tail Whip, Bubble |
| [0:06:31](https://www.youtube.com/watch?v=CbfjWuRWH10&t=391) | route1-rattata-capture | 7 | Tackle, Tail Whip, Bubble | Tackle, Tail Whip, Bubble |
| [0:08:47](https://www.youtube.com/watch?v=CbfjWuRWH10&t=527) | forest-caterpie4-flee | 7 | Tackle, Tail Whip, Bubble | Tackle, Tail Whip, Bubble |
| [0:09:00](https://www.youtube.com/watch?v=CbfjWuRWH10&t=540) | forest-kakuna-flee | 7 | Tackle, Tail Whip, Bubble | Tackle, Tail Whip, Bubble |
| [0:09:16](https://www.youtube.com/watch?v=CbfjWuRWH10&t=556) | forest-caterpie5-flee | 7 | Tackle, Tail Whip, Bubble | Tackle, Tail Whip, Bubble |
| [0:09:35](https://www.youtube.com/watch?v=CbfjWuRWH10&t=575) | forest-sammy | 7 | Tackle, Tail Whip, Bubble | Tackle, Tail Whip, Bubble |
| [0:10:56](https://www.youtube.com/watch?v=CbfjWuRWH10&t=656) | pewter-liam | 8 | Tackle, Tail Whip, Bubble | Tackle, Tail Whip, Bubble, Withdraw |
| [0:12:10](https://www.youtube.com/watch?v=CbfjWuRWH10&t=730) | brock | 11 | Tackle, Tail Whip, Bubble, Withdraw | Tackle, Water Gun, Bubble, Withdraw |
| [0:14:33](https://www.youtube.com/watch?v=CbfjWuRWH10&t=873) | route3-colton | 13 | Tackle, Water Gun, Bubble, Withdraw | Tackle, Water Gun, Bubble, Withdraw |
| [0:15:25](https://www.youtube.com/watch?v=CbfjWuRWH10&t=925) | route3-greg | 14 | Tackle, Water Gun, Bubble, Withdraw | Tackle, Water Gun, Bubble, Withdraw |
| [0:16:25](https://www.youtube.com/watch?v=CbfjWuRWH10&t=985) | route3-james | 15 | Tackle, Water Gun, Bubble, Withdraw | Tackle, Water Gun, Bubble, Withdraw |
| [0:17:00](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1020) | route3-pidgey-capture | 15 | Tackle, Water Gun, Bubble, Withdraw | Tackle, Water Gun, Bubble, Withdraw |
| [0:18:16](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1096) | mtmoon-josh | 15 | Tackle, Water Gun, Bubble, Withdraw | Tackle, Water Gun, Bubble, Withdraw |
| [0:20:00](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1200) | mtmoon-rocket | 16 | Tackle, Water Gun, Bubble, Withdraw | Tackle, Water Gun, Bubble, Withdraw |
| [0:20:40](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1240) | mtmoon-miguel | 16 | Tackle, Water Gun, Bubble, Withdraw | Tackle, Water Gun, Bubble, Withdraw |
| [0:23:29](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1409) | misty | 20 | Tackle, Water Gun, Bite, Mega Kick | Tackle, Water Gun, Bite, Mega Kick |
| [0:25:18](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1518) | cerulean-rival | 21 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:26:49](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1609) | bridge-cale | 22 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:27:45](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1665) | bridge-ali | 22 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:28:33](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1713) | bridge-timmy | 23 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:29:10](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1750) | bridge-reli | 23 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:29:43](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1783) | bridge-ethan | 23 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:30:21](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1821) | bridge-rocket | 23 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:31:09](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1869) | route25-wayne | 24 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:31:37](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1897) | route25-kelsey | 24 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:32:12](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1932) | route25-flint | 24 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:32:57](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1977) | route25-haley | 24 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:35:10](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2110) | cerulean-dig-rocket | 25 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:36:48](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2208) | route6-jeff | 25 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:38:06](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2286) | ssanne-rival | 27 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:41:20](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2480) | vermilion-tucker | 28 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:42:24](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2544) | surge | 28 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:45:27](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2727) | route9-alicia | 28 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:46:43](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2803) | route9-conner | 29 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:47:47](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2867) | rocktunnel-ashton | 29 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:48:52](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2932) | rocktunnel-winston | 30 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:49:12](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2952) | rocktunnel-martha | 30 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:49:46](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2986) | rocktunnel-allen | 30 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:50:21](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3021) | rocktunnel-oliver | 30 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:51:39](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3099) | rocktunnel-sofia | 31 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:52:20](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3140) | rocktunnel-dudley | 31 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:53:10](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3190) | rocktunnel-dana | 32 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:54:30](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3270) | route8-rich | 32 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:55:47](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3347) | hideout-poster-guard | 32 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:56:51](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3411) | hideout-key-grunt | 32 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:58:10](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3490) | hideout-left-guard | 33 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [0:59:02](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3542) | hideout-right-guard | 33 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:01:05](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3665) | hideout-giovanni | 36 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:04:12](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3852) | tower-rival | 36 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:06:36](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3996) | tower-tammy | 37 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:07:00](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4020) | tower-jennifer | 37 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:07:28](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4048) | tower-emilia | 37 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:08:04](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4084) | tower-marowak | 37 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:08:32](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4112) | tower-rocket1 | 38 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:09:20](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4160) | tower-rocket2 | 38 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:10:12](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4212) | tower-rocket3 | 38 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:11:57](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4317) | route16-snorlax | 38 | Water Pulse, Water Gun, Bite, Mega Kick | Water Pulse, Water Gun, Bite, Mega Kick |
| [1:15:14](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4514) | fuchsia-kirk | 38 | Water Pulse, Surf, Bite, Mega Kick | Water Pulse, Surf, Bite, Mega Kick |
| [1:16:34](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4594) | koga | 39 | Water Pulse, Surf, Bite, Mega Kick | Water Pulse, Surf, Bite, Mega Kick |
| [1:21:44](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4904) | blaine | 40 | Water Pulse, Surf, Bite, Mega Kick | Water Pulse, Surf, Bite, Mega Kick |
| [1:24:11](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5051) | celadon-tamia | 41 | Water Pulse, Surf, Bite, Mega Kick | Water Pulse, Surf, Bite, Mega Kick |
| [1:25:30](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5130) | celadon-lori | 44 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:26:04](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5164) | erika | 44 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:28:54](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5334) | silph-rival | 44 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:31:00](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5460) | silph-boardroom-grunt | 45 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:31:54](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5514) | silph-giovanni | 46 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:33:30](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5610) | sabrina | 46 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:35:13](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5713) | viridian-takashi | 47 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:36:08](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5768) | viridian-warren | 48 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:37:31](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5851) | giovanni-gym | 48 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:39:50](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5990) | route22-rival | 49 | Water Pulse, Surf, Bite, Blizzard | Water Pulse, Surf, Bite, Blizzard |
| [1:46:37](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6397) | lorelei | 51 | Strength, Surf, Bite, Blizzard | Strength, Surf, Bite, Blizzard |
| [1:49:15](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6555) | bruno | 52 | Strength, Surf, Bite, Blizzard | Strength, Surf, Bite, Blizzard |
| [1:51:12](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6672) | agatha | 53 | Strength, Surf, Bite, Blizzard | Strength, Surf, Bite, Blizzard |
| [1:53:07](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6787) | lance | 54 | Strength, Surf, Bite, Blizzard | Strength, Surf, Bite, Blizzard |
| [1:55:44](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6944) | champion | 55 | Strength, Surf, Bite, Blizzard | Strength, Surf, Bite, Blizzard |

## Slot-order observations

- Tackle and Tail Whip are swapped during the Pidgey fight at 4:01–4:02; membership is unchanged.
- After Water Gun replaces slot 1 at Brock, Tackle and Water Gun are reordered before the 22:07 tutor menu. The exact reorder input/time is not isolated.
- Water Pulse and Water Gun have swapped by the 51:48 Sofia menu. The exact reorder input/time is not isolated.

Six recorded full-menu checks match the reconstructed move membership. Source lines and evidence are in moves.json; learnset levels come from pret. Received TMs/HMs are not treated as learned until the teaching event. Cut on Rattata and Fly on Pidgey do not change the lead's moves.
