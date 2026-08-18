"""Diagnosis for improvement slice 2 — where invest-then-fold actually comes from.

Run it against an analytics export produced by `backend/tools/export_analytics.py`:

    cd backend && PYTHONPATH=. python -m tools.export_analytics \
        --hands 50000 --seed 20260817 --out /tmp/sim50k
    python docs/ai-dlc/research/slice2-invest-then-fold/diagnose.py /tmp/sim50k 50000

This is evidence for a spec, not a gate and not a standing harness. It adds no
apparatus: it reads the existing export contract and prints, and it is expected
to be re-run by hand if anyone wants to check the numbers in
`docs/ai-dlc/specs/phase3-invest-then-fold.md`.

The statistic it reproduces is the one the 2026-08-05 re-measure reported as
"invest-then-fold", defined in that study's own script
(`persona-realism-artifacts/remeasure-2026-08-05/agent-scripts/commitment.py`)
as: a fold where the seat has already committed at least 25bb in the hand and
is being offered pot odds of at least 5:1, that is
`to_call / (pot_before + to_call) <= 1/6`. `pot_before` already contains the
aggressor's bet, so that ratio is the caller's share of the pot it would win.
"""
import collections
import sys

import pyarrow.parquet as pq

SIM = sys.argv[1]
N_HANDS = int(sys.argv[2])

so = pq.read_table(f"{SIM}/seat_outcomes.parquet").to_pydict()
dc = pq.read_table(f"{SIM}/decisions.parquet").to_pydict()

seat_info = {(h, s): (p, st) for h, s, p, st in
             zip(so["hand_id"], so["seat"], so["persona"], so["starting_stack_bb"])}
seats_per_persona = collections.Counter(so["persona"])
n_allin_in_hand = collections.Counter()
for hid, fs in zip(so["hand_id"], so["final_status"]):
    if fs == "allin":
        n_allin_in_hand[hid] += 1

B = collections.defaultdict(collections.Counter)
by_node = collections.Counter()
by_street = collections.Counter()
faced_band = collections.Counter()
size_bucket_of_faced = collections.Counter()
allin_call = near_allin = total = 0
pot_sizes = []
allin_seats_present = collections.Counter()
agg_share_all = []
agg_share_by_persona = collections.defaultdict(list)
never_aggressed = 0
biggest_commit_node = collections.Counter()
biggest_commit_street = collections.Counter()

order = sorted(range(len(dc["hand_id"])), key=lambda i: (dc["hand_id"][i], dc["seq"][i]))
committed = collections.defaultdict(float)
agg_chips = collections.defaultdict(float)
biggest = collections.defaultdict(lambda: (0.0, "?", "?|?", "?"))
prev_hand = None
for i in order:
    hid = dc["hand_id"][i]
    if hid != prev_hand:
        committed.clear(); agg_chips.clear(); biggest.clear()
        prev_hand = hid
    seat = dc["seat"][i]
    info = seat_info.get((hid, seat))
    act = dc["action"][i]
    tc = dc["to_call_bb"][i] or 0.0
    pot = dc["pot_before_bb"][i] or 0.0
    chips = dc["chips_committed_bb"][i] or 0.0
    if info and act == "fold":
        persona, stack = info
        inv = committed[seat]
        odds = tc / (pot + tc) if (pot + tc) else 1.0
        B[persona]["folds"] += 1
        if inv >= 25.0:
            B[persona]["fold_after_25bb"] += 1
            if odds <= 1 / 6:
                B[persona]["classB"] += 1
                total += 1
                street = dc["street"][i]
                hcb = dc["hand_class_bucket"][i] or "?|?"
                made, _, draw = hcb.partition("|")
                by_street[street] += 1
                by_node[(street, made, draw)] += 1
                pre = max(pot - tc, 0.01)
                f = tc / pre
                faced_band["f <= 0.10" if f <= 0.10 else
                           "0.10 < f <= 0.25" if f <= 0.25 else
                           "0.25 < f <= 0.40" if f <= 0.40 else "f > 0.40"] += 1
                size_bucket_of_faced["SMALL" if f <= 0.40 else
                                     "MEDIUM" if f <= 0.70 else
                                     "LARGE" if f <= 1.10 else "OVERBET"] += 1
                remaining = stack - inv
                if tc >= remaining - 0.01:
                    allin_call += 1
                elif tc >= 0.9 * remaining:
                    near_allin += 1
                pot_sizes.append(pot)
                allin_seats_present[n_allin_in_hand[hid]] += 1
                share = agg_chips[seat] / inv if inv else 0.0
                agg_share_all.append(share)
                agg_share_by_persona[persona].append(share)
                if agg_chips[seat] == 0.0:
                    never_aggressed += 1
                _, bst, bhcb, bact = biggest[seat]
                biggest_commit_node[f"{bhcb} via {bact}"] += 1
                biggest_commit_street[bst] += 1
    committed[seat] += chips
    if act in ("bet", "raise"):
        agg_chips[seat] += chips
    if chips > biggest[seat][0] and act != "post":
        biggest[seat] = (chips, dc["street"][i], dc["hand_class_bucket"][i] or "?|?", act)

pct = lambda c: 100 * c / max(total, 1)
PERS = ["maniac", "calling_station", "passive_fish", "lag", "tag", "nit"]

print(f"=== invest-then-fold on {SIM} ({N_HANDS} hands) ===\n")
print(f"{'persona':17} {'folds':>7} {'fold>=25bb':>11} {'events':>7} "
      f"{'conditional':>12} {'per 1k hands':>13}")
for p in PERS:
    b = B[p]
    seats = seats_per_persona[p] / N_HANDS
    print(f"{p:17} {b['folds']:7d} {b['fold_after_25bb']:11d} {b['classB']:7d} "
          f"{100*b['classB']/max(b['fold_after_25bb'],1):11.1f}% "
          f"{1000*b['classB']/(N_HANDS*seats):12.2f}")
print(f"\ntotal events: {total}")

print(f"\n--- is the fold a refusal to call an all-in? ---")
print(f"call would be all-in (to_call >= remaining stack): {allin_call} ({pct(allin_call):.1f}%)")
print(f"call would be >=90% of the remaining stack: {near_allin} ({pct(near_allin):.1f}%)")
pot_sizes.sort()
if pot_sizes:
    q = lambda x: pot_sizes[min(int(x * len(pot_sizes)), len(pot_sizes) - 1)]
    print(f"pot before the fold (bb): min {pot_sizes[0]:.0f}  p25 {q(.25):.0f}  "
          f"median {q(.5):.0f}  p75 {q(.75):.0f}  max {pot_sizes[-1]:.0f}")
print("seats already all-in in that hand:")
for k, v in sorted(allin_seats_present.items()):
    print(f"  {k}: {v:5d} ({pct(v):5.1f}%)")
n_with_allin = sum(1 for h in set(dc["hand_id"]) if n_allin_in_hand[h] > 0)
print(f"hands with at least one all-in seat: {n_with_allin}/{N_HANDS} "
      f"({100*n_with_allin/N_HANDS:.1f}%)")

print(f"\n--- which decision node ---")
for s, c in by_street.most_common():
    print(f"  street {s:8} {c:6d} ({pct(c):5.1f}%)")
print("  top nodes (street, made hand, draw):")
for (s, made, draw), c in by_node.most_common(10):
    print(f"    {s:8} {made:14} draw={draw:7} {c:6d} ({pct(c):5.1f}%)")
hard_zero = sum(c for (s, m, d), c in by_node.items()
                if s == "river" and m in ("air", "ace_high") and d == "none")
print(f"  river + (air or ace-high) + no draw — the cell where call merit is "
      f"hard-zeroed: {hard_zero} ({pct(hard_zero):.1f}%)")

print(f"\n--- the price being refused ---")
for k in ["f <= 0.10", "0.10 < f <= 0.25", "0.25 < f <= 0.40", "f > 0.40"]:
    print(f"  {k:18} {faced_band[k]:6d} ({pct(faced_band[k]):5.1f}%)")
print("  RES-E size bucket of the faced bet:")
for k in ["SMALL", "MEDIUM", "LARGE", "OVERBET"]:
    print(f"    {k:8} {size_bucket_of_faced[k]:6d} ({pct(size_bucket_of_faced[k]):5.1f}%)")

print(f"\n--- how did the money get in? ---")
agg_share_all.sort()
n = len(agg_share_all)
if n:
    q = lambda x: agg_share_all[min(int(x * n), n - 1)]
    print(f"share of the investment that went in as a bet or raise: "
          f"p25 {q(.25):.2f}  median {q(.5):.2f}  p75 {q(.75):.2f}  "
          f"mean {sum(agg_share_all)/n:.2f}")
print(f"never bet or raised at all this hand: {never_aggressed} ({pct(never_aggressed):.1f}%)")
print("per-persona mean aggressive share:")
for p in PERS:
    v = agg_share_by_persona[p]
    if v:
        print(f"  {p:17} n={len(v):5d}  {sum(v)/len(v):.2f}")
print("street of the seat's single largest commitment:")
for s, c in biggest_commit_street.most_common():
    print(f"  {s:9} {c:6d} ({pct(c):5.1f}%)")
print("hand class and action at that largest commitment — top 8:")
for k, c in biggest_commit_node.most_common(8):
    print(f"  {k:34} {c:6d} ({pct(c):5.1f}%)")

print(f"\n--- how many of the events are not decisions at all? ---")
forced = 0
com2 = collections.defaultdict(float)
prev2 = None
for i in order:
    hid = dc["hand_id"][i]
    if hid != prev2:
        com2.clear(); prev2 = hid
    seat = dc["seat"][i]
    info = seat_info.get((hid, seat))
    tc = dc["to_call_bb"][i] or 0.0
    pot = dc["pot_before_bb"][i] or 0.0
    if info and dc["action"][i] == "fold":
        _, stack = info
        inv = com2[seat]
        odds = tc / (pot + tc) if (pot + tc) else 1.0
        if inv >= 25.0 and odds <= 1 / 6 and dc["street"][i] == "river" \
                and (dc["hand_class_bucket"][i] or "") in ("air|none", "ace_high|none") \
                and tc >= (stack - inv) - 0.01:
            forced += 1
    com2[seat] += (dc["chips_committed_bb"][i] or 0.0)
print(f"river air/ace-high with no draw, facing a bet at least as big as the stack: "
      f"{forced} ({pct(forced):.1f}%)")
print("  `table/engine.py` offers no RAISE without headroom above the current bet, and")
print("  `personas_postflop.py:1010` sets call_merit to 0.0 for that cell, so FOLD is the")
print("  only candidate with any weight: P(fold) = 1.000 exactly, not a mixed strategy.")

print(f"\n--- collision with slice 3 (calldown) ---")
saw = collections.Counter(); sd = collections.Counter()
for p, sf, ws in zip(so["persona"], so["saw_flop"], so["went_to_showdown"]):
    if sf:
        saw[p] += 1
        sd[p] += ws
river_hz = collections.Counter()
for i in range(len(dc["hand_id"])):
    if dc["action"][i] == "fold" and dc["street"][i] == "river" and \
            (dc["hand_class_bucket"][i] or "") in ("air|none", "ace_high|none"):
        info = seat_info.get((dc["hand_id"][i], dc["seat"][i]))
        if info:
            river_hz[info[0]] += 1
saw_all, sd_all, hz_all = sum(saw.values()), sum(sd.values()), sum(river_hz.values())
print(f"{'persona':17} {'saw flop':>9} {'WTSD':>7} {'river hard-zero folds':>22} "
      f"{'WTSD if they called':>20}")
for p in PERS:
    if saw[p]:
        print(f"{p:17} {saw[p]:9d} {100*sd[p]/saw[p]:6.1f}% {river_hz[p]:22d} "
              f"{100*(sd[p]+river_hz[p])/saw[p]:19.1f}%")
print(f"{'POOL':17} {saw_all:9d} {100*sd_all/saw_all:6.1f}% {hz_all:22d} "
      f"{100*(sd_all+hz_all)/saw_all:19.1f}%")
river_air = sum(1 for i in range(len(dc["hand_id"]))
                if dc["action"][i] == "fold" and dc["street"][i] == "river"
                and (dc["hand_class_bucket"][i] or "") == "air|none")
river_ah = hz_all - river_air
print(f"\nsplit of the {hz_all} river hard-zero folds, because the cell bundles two hands:")
print(f"  air        {river_air:5d}  upper-bound WTSD if all called "
      f"{100*(sd_all+river_air)/saw_all:5.2f}%  (+{100*river_air/saw_all:.2f}pp)")
print(f"  ace-high   {river_ah:5d}  upper-bound WTSD if all called "
      f"{100*(sd_all+river_ah)/saw_all:5.2f}%  (+{100*river_ah/saw_all:.2f}pp)")
print("  These are UPPER BOUNDS. They assume every fold becomes a call, which the merit")
print("  law would not do, and they ignore the bettor's own seat-hand.")
print("WTSD here is the analytics definition — seat-hands reaching showdown over "
      "seat-hands seeing the flop (poker-analytics scorer/stats.py). The pool "
      "target is 27.0 with sigma 2.73.")
