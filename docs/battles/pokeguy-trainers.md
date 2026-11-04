# Pokeguy trainer win-rate estimates

All 69 trainer fights, each reset to its recorded entry state. These are model estimates for our `solo-setup-heal/4` policy, not measurements of Pokeguy’s play or a whole-run completion probability.

Seed 1; 31540 trials in total. Intervals have 95% simultaneous coverage across all 69 battles and all adaptive sampling looks, conditional on the model. The target is a total interval width of 10 percentage points; the per-case cap is 3,000 trials and the turn limit is 300.

See [method, inputs and limitations](pokeguy-benchmark.md), [machine-readable summary](pokeguy-trainers.json), and [starting states](../progression/pokeguy-states.md). An all-win sample still has a lower bound below 100%.

| Battle | Level | HP on entry | Wins / trials | Estimate | Simultaneous interval | Stop |
|---|---:|---:|---:|---:|---:|---|
| [lab-rival](https://www.youtube.com/watch?v=CbfjWuRWH10&t=117) | 5 | 20/20 | 345/360 | 95.8% | 89.2%–99.0% | interval_width |
| [forest-sammy](https://www.youtube.com/watch?v=CbfjWuRWH10&t=575) | 7 | 16/25 | 781/880 | 88.8% | 83.2%–93.1% | interval_width |
| [pewter-liam](https://www.youtube.com/watch?v=CbfjWuRWH10&t=656) | 8 | 5/27 | 1332/2000 | 66.6% | 61.5%–71.5% | interval_width |
| [brock](https://www.youtube.com/watch?v=CbfjWuRWH10&t=730) | 11 | 11/33 | 1176/2260 | 52.0% | 47.0%–57.0% | interval_width |
| [route3-colton](https://www.youtube.com/watch?v=CbfjWuRWH10&t=873) | 13 | 6/38 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route3-greg](https://www.youtube.com/watch?v=CbfjWuRWH10&t=925) | 14 | 8/40 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route3-james](https://www.youtube.com/watch?v=CbfjWuRWH10&t=985) | 15 | 10/42 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [mtmoon-josh](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1096) | 15 | 10/42 | 966/1140 | 84.7% | 79.3%–89.3% | interval_width |
| [mtmoon-rocket](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1200) | 16 | 10/49 | 158/160 | 98.8% | 90.3%–100.0% | interval_width |
| [mtmoon-miguel](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1240) | 16 | 10/49 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [misty](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1409) | 20 | 54/59 | 177/180 | 98.3% | 90.1%–100.0% | interval_width |
| [cerulean-rival](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1518) | 21 | 32/61 | 917/2200 | 41.7% | 36.8%–46.7% | interval_width |
| [bridge-cale](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1609) | 22 | 22/64 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [bridge-ali](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1665) | 22 | 22/64 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [bridge-timmy](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1713) | 23 | 24/66 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [bridge-reli](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1750) | 23 | 24/66 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [bridge-ethan](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1783) | 23 | 24/66 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [bridge-rocket](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1821) | 23 | 24/66 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route25-wayne](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1869) | 24 | 27/69 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route25-kelsey](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1897) | 24 | 27/69 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route25-flint](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1932) | 24 | 27/69 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route25-haley](https://www.youtube.com/watch?v=CbfjWuRWH10&t=1977) | 24 | 27/69 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [cerulean-dig-rocket](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2110) | 25 | 27/72 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route6-jeff](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2208) | 25 | 21/72 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [ssanne-rival](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2286) | 27 | 37/76 | 1100/2260 | 48.7% | 43.7%–53.7% | interval_width |
| [vermilion-tucker](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2480) | 28 | 79/79 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [surge](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2544) | 28 | 79/79 | 1263/2200 | 57.4% | 52.4%–62.4% | interval_width |
| [route9-alicia](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2727) | 28 | 43/79 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route9-conner](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2803) | 29 | 45/81 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [rocktunnel-ashton](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2867) | 29 | 45/81 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [rocktunnel-winston](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2932) | 30 | 42/84 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [rocktunnel-martha](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2952) | 30 | 39/84 | 215/220 | 97.7% | 90.1%–99.9% | interval_width |
| [rocktunnel-allen](https://www.youtube.com/watch?v=CbfjWuRWH10&t=2986) | 30 | 39/84 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [rocktunnel-oliver](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3021) | 30 | 39/84 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [rocktunnel-sofia](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3099) | 31 | 41/86 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [rocktunnel-dudley](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3140) | 31 | 41/86 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [rocktunnel-dana](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3190) | 32 | 44/89 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route8-rich](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3270) | 32 | 39/89 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [hideout-poster-guard](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3347) | 32 | 39/89 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [hideout-key-grunt](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3411) | 32 | 39/89 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [hideout-left-guard](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3490) | 33 | 42/92 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [hideout-right-guard](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3542) | 33 | 42/92 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [hideout-giovanni](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3665) | 36 | 38/114 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [tower-rival](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3852) | 36 | 38/114 | 177/180 | 98.3% | 90.1%–100.0% | interval_width |
| [tower-tammy](https://www.youtube.com/watch?v=CbfjWuRWH10&t=3996) | 37 | 24/116 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [tower-jennifer](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4020) | 37 | 24/116 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [tower-emilia](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4048) | 37 | 24/116 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [tower-rocket1](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4112) | 38 | 27/119 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [tower-rocket2](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4160) | 38 | 27/119 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [tower-rocket3](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4212) | 38 | 27/119 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [fuchsia-kirk](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4514) | 38 | 31/119 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [koga](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4594) | 39 | 34/122 | 916/2200 | 41.6% | 36.7%–46.7% | interval_width |
| [blaine](https://www.youtube.com/watch?v=CbfjWuRWH10&t=4904) | 40 | 24/126 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [celadon-tamia](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5051) | 41 | 26/128 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [celadon-lori](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5130) | 44 | 35/137 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [erika](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5164) | 44 | 35/137 | 453/480 | 94.4% | 88.2%–98.0% | interval_width |
| [silph-rival](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5334) | 44 | 85/137 | 704/780 | 90.3% | 84.6%–94.4% | interval_width |
| [silph-boardroom-grunt](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5460) | 45 | 30/140 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [silph-giovanni](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5514) | 46 | 33/143 | 638/700 | 91.1% | 85.3%–95.3% | interval_width |
| [sabrina](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5610) | 46 | 33/143 | 177/180 | 98.3% | 90.1%–100.0% | interval_width |
| [viridian-takashi](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5713) | 47 | 25/146 | 139/140 | 99.3% | 90.7%–100.0% | interval_width |
| [viridian-warren](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5768) | 48 | 28/149 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [giovanni-gym](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5851) | 48 | 28/149 | 100/100 | 100.0% | 90.4%–100.0% | interval_width |
| [route22-rival](https://www.youtube.com/watch?v=CbfjWuRWH10&t=5990) | 49 | 153/153 | 757/2080 | 36.4% | 31.5%–41.5% | interval_width |
| [lorelei](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6397) | 51 | 159/159 | 309/320 | 96.6% | 89.9%–99.4% | interval_width |
| [bruno](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6555) | 52 | 130/162 | 582/1900 | 30.6% | 25.8%–35.8% | interval_width |
| [agatha](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6672) | 53 | 45/165 | 399/420 | 95.0% | 88.6%–98.5% | interval_width |
| [lance](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6787) | 54 | 168/168 | 1215/1580 | 76.9% | 71.7%–81.6% | interval_width |
| [champion](https://www.youtube.com/watch?v=CbfjWuRWH10&t=6944) | 55 | 171/171 | 1246/2220 | 56.1% | 51.1%–61.1% | interval_width |

0 turn-limit outcomes counted as non-wins. Wild/scripted fights, captures and escapes are outside this trainer report. The selected profile uses Mild and Attack IV25; engine/AI and input uncertainty are not included in the sampling intervals.
