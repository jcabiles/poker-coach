"""T3 measurement harness — every number the T3 provenance blocks cite.

Run it against analytics exports produced by `backend/tools/export_analytics.py`.
**`--lineup` is mandatory and is not the exporter default**, for the reason
`diagnose.py`'s header gives: counts taken on any other table are comparable
with nothing.

    cd backend && PYTHONPATH=. python -m tools.export_analytics \
        --hands 50000 --seed 20260817 \
        --lineup tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac \
        --out /tmp/sim50k-t3
    python docs/ai-dlc/research/slice2-invest-then-fold/t3_measure.py /tmp/sim50k-t3

This exists because T3's first round put every number behind untracked scripts,
and a stale figure (P(call) 0.691, measured before the owner's band ruling and
never re-measured) survived into a committed comment where no reader could check
it. Anything a source comment cites has to be somewhere a reader can open. The
committed output table is `t3-measurements.md` beside this file.

Six sections, matching the six things the source and the pull request claim:

1. THE DETERMINISM CRITERION. Two different statistics get called "the criterion"
   and they are reconciled here rather than chosen between. `diagnose.py`'s final
   line counts FOLDS in the invest-then-fold class at a node where the engine
   offers no raise; that count includes ace-high folds which are now outcomes of
   a MIXED decision. The determinism statistic is the same count restricted to
   AIR, the only bucket still hard-zeroed, because those are the only folds that
   are probability-1.000 by construction.
2. THE HEADLINE NODE. Every decision (not only folds) where the faced bet is at
   least the seat's remaining stack, split by bucket and by persona.
3. MINIMUM-DEFENCE ARITHMETIC. The range continue rate over all river
   facing-chips decisions against the mean of 1/(1+f), which is what the damp
   constant was derived from.
4. PRICE AND REALIZED EQUITY. The faced-size distribution, and what naked
   ace-high actually wins when it calls — the finding that the derived value is
   right against a balanced opponent and wrong against this field.
5. MULTIWAY. Opponent count reconstructed from the decisions stream, because the
   export carries no `opponents` column.
6. POOL WENT-TO-SHOWDOWN, the metric the 3.78-point bound is stated against.
"""
import collections
import json
import sys

import pyarrow.parquet as pq

RATIFIED = ["tag", "tag", "calling_station", "tag", "passive_fish",
            "lag", "passive_fish", "nit", "maniac"]
PERSONAS = ["maniac", "calling_station", "passive_fish", "lag", "tag", "nit"]
BUCKETS = ("ace_high|none", "air|none")


def provenance(sim):
    try:
        with open(f"{sim}/_SUCCESS") as fh:
            m = json.load(fh)
    except (OSError, ValueError):
        print("!! no readable _SUCCESS manifest — provenance unknown\n")
        return
    lineup = [m["lineup"][k] for k in sorted(m.get("lineup") or {}, key=int)]
    print(f"export     : {sim}")
    print(f"seed       : {m.get('seed')}")
    print(f"engine sha : {m.get('git_sha')}")
    print(f"lineup     : {','.join(lineup)}")
    print("             ^ the ratified lineup" if lineup == RATIFIED else
          "!!           ^ NOT the ratified lineup — every count below is "
          "specific to this table")
    print()


def main(sim):
    so = pq.read_table(f"{sim}/seat_outcomes.parquet").to_pydict()
    dc = pq.read_table(f"{sim}/decisions.parquet").to_pydict()
    info = {(h, s): (p, st) for h, s, p, st in
            zip(so["hand_id"], so["seat"], so["persona"], so["starting_stack_bb"])}
    outcome = {(h, s): d for h, s, d in
               zip(so["hand_id"], so["seat"], so["delta_bb"])}
    order = sorted(range(len(dc["hand_id"])),
                   key=lambda i: (dc["hand_id"][i], dc["seq"][i]))

    itf_folds = collections.Counter()          # section 1
    node = collections.defaultdict(collections.Counter)          # section 2
    node_by_persona = collections.defaultdict(collections.Counter)
    river_by_bucket = collections.defaultdict(collections.Counter)  # section 3
    mdf_num = n_river = 0                                            # section 3
    fs = []                                                          # section 4
    band_calls = collections.defaultdict(lambda: [0, 0])             # section 4
    req_equity = []                                                  # section 4
    by_opp = collections.defaultdict(collections.Counter)            # section 5

    committed = collections.defaultdict(float)
    folded, prev = set(), None
    for i in order:
        hid = dc["hand_id"][i]
        if hid != prev:
            committed.clear()
            folded = set()
            prev = hid
        seat, act = dc["seat"][i], dc["action"][i]
        tc = dc["to_call_bb"][i] or 0.0
        pot = dc["pot_before_bb"][i] or 0.0
        hcb = dc["hand_class_bucket"][i] or ""
        who = info.get((hid, seat))
        if who and dc["street"][i] == "river" and tc > 0.0 and act != "post":
            persona, stack = who
            remaining = stack - committed[seat]
            pre = max(pot - tc, 0.01)
            f = tc / pre
            river_by_bucket[hcb][act] += 1
            mdf_num += 1.0 / (1.0 + f)
            n_river += 1
            if hcb in BUCKETS:
                by_opp[(hcb, 8 - len(folded - {seat}))][act] += 1
                if tc >= remaining - 0.01:
                    node[hcb][act] += 1
                    node_by_persona[(persona, hcb)][act] += 1
                    if (act == "fold" and committed[seat] >= 25.0
                            and tc / (pot + tc) <= 1 / 6):
                        itf_folds[hcb] += 1
            if hcb == "ace_high|none":
                fs.append(f)
                req_equity.append(tc / (pot + tc))
                band = ("f<=0.25" if f <= 0.25 else "0.25<f<=0.50" if f <= 0.50
                        else "0.50<f<=0.85" if f <= 0.85 else "f>0.85")
                band_calls[band][0] += 1
                if act == "call":
                    band_calls[band][1] += 1
        committed[seat] += (dc["chips_committed_bb"][i] or 0.0)
        if act == "fold":
            folded.add(seat)

    provenance(sim)

    print("=== 1. the determinism criterion, both statistics ===")
    print("  (a) `diagnose.py`'s printed count — river air/ace-high no-draw FOLDS")
    print("      in the invest-then-fold class facing a bet >= the remaining stack:")
    for b in BUCKETS:
        print(f"        {b:14} {itf_folds[b]:5d}")
    print(f"        {'total':14} {sum(itf_folds.values()):5d}")
    print("  (b) folds that are PROBABILITY-1.000 BY CONSTRUCTION — the same")
    print("      filter restricted to AIR, the only bucket still hard-zeroed:")
    print(f"        {itf_folds['air|none']:5d}")
    print("      The ace-high folds in (a) are outcomes of a mixed decision and")
    print("      are NOT determinism; before T3 every fold in (a) was in (b).")

    print("\n=== 2. the headline node — every decision, no raise offered ===")
    for b in BUCKETS:
        c = node[b]
        n = sum(c.values())
        print(f"  {b:14} n={n:5d} fold={c['fold']:5d} call={c['call']:5d} "
              f"P(call)={c['call'] / max(n, 1):.4f}")
        for p in PERSONAS:
            pc = node_by_persona[(p, b)]
            pn = sum(pc.values())
            if pn:
                print(f"    {p:16} n={pn:5d} fold={pc['fold']:5d} "
                      f"call={pc['call']:5d} P(call)={pc['call'] / pn:.4f}")

    print("\n=== 3. minimum-defence arithmetic (the derivation's input) ===")
    tot = collections.Counter()
    for c in river_by_bucket.values():
        tot.update(c)
    N = sum(tot.values())
    cont = tot["call"] + tot["raise"]
    mdf = mdf_num / max(n_river, 1)
    print(f"  river facing-chips decisions : {N}")
    print(f"  mean faced size f            : {sum(fs) / max(len(fs), 1):.4f} "
          f"(ace-high subset)")
    print(f"  MDF = mean of 1/(1+f)        : {mdf:.4f}")
    print(f"  range continue (call+raise)  : {cont}/{N} = {cont / N:.4f}")
    print(f"  shortfall against MDF        : {mdf - cont / N:+.4f}")
    print(f"  {'bucket':22} {'n':>6} {'share':>7} {'continue':>9}")
    for k in sorted(river_by_bucket, key=lambda k: -sum(river_by_bucket[k].values())):
        c = river_by_bucket[k]
        m = sum(c.values())
        print(f"  {k:22} {m:6d} {100 * m / N:6.1f}% "
              f"{(c['call'] + c['raise']) / m:9.4f}")

    print("\n=== 4. price faced, and what the calls actually win ===")
    fs.sort()
    req_equity.sort()
    def q(v, x):
        return v[min(int(x * len(v)), len(v) - 1)] if v else 0.0
    print(f"  faced size f    : p10 {q(fs, .1):.3f}  median {q(fs, .5):.3f}  "
          f"p90 {q(fs, .9):.3f}  mean {sum(fs) / max(len(fs), 1):.3f}")
    print(f"  required equity : p10 {q(req_equity, .1):.3f}  "
          f"median {q(req_equity, .5):.3f}  "
          f"mean {sum(req_equity) / max(len(req_equity), 1):.3f}")
    print(f"  {'faced band':14} {'n':>6} {'calls':>6} {'P(call)':>9}")
    for b in ("f<=0.25", "0.25<f<=0.50", "0.50<f<=0.85", "f>0.85"):
        n, c = band_calls[b]
        if n:
            print(f"  {b:14} {n:6d} {c:6d} {c / n:9.4f}")
    won = calls = 0
    band_win = collections.defaultdict(lambda: [0, 0])
    eq = []
    for i in range(len(dc["hand_id"])):
        if (dc["street"][i] == "river"
                and (dc["hand_class_bucket"][i] or "") == "ace_high|none"
                and dc["action"][i] == "call" and (dc["to_call_bb"][i] or 0.0) > 0.0):
            tc = dc["to_call_bb"][i]
            pot = dc["pot_before_bb"][i] or 0.0
            f = tc / max(pot - tc, 0.01)
            band = ("f<=0.25" if f <= 0.25 else "0.25<f<=0.50" if f <= 0.50
                    else "0.50<f<=0.85" if f <= 0.85 else "f>0.85")
            calls += 1
            eq.append(tc / (pot + tc))
            w = (outcome.get((dc["hand_id"][i], dc["seat"][i])) or 0.0) > 0.0
            won += bool(w)
            band_win[band][0] += 1
            band_win[band][1] += bool(w)
    if calls:
        print(f"  calls made {calls}; mean required equity of those calls "
              f"{sum(eq) / len(eq):.4f}; realized win rate {won / calls:.4f} "
              f"({won}/{calls})")
        for b in ("f<=0.25", "0.25<f<=0.50", "0.50<f<=0.85", "f>0.85"):
            n, w = band_win[b]
            if n:
                print(f"    {b:14} calls {n:5d}  win rate {w / n:.4f}")

    print("\n=== 5. multiway (opponent count rebuilt from the decisions stream) ===")
    for b in BUCKETS:
        hu = by_opp[(b, 1)]
        mw = collections.Counter()
        for (bb, k), c in by_opp.items():
            if bb == b and k > 1:
                mw.update(c)
        for label, c in (("heads-up", hu), ("multiway", mw)):
            n = sum(c.values())
            print(f"  {b:14} {label:9} n={n:5d} P(call)={c['call'] / max(n, 1):.4f}")

    print("\n=== 6. pool went-to-showdown ===")
    saw = sd = 0
    for sf, ws in zip(so["saw_flop"], so["went_to_showdown"]):
        if sf:
            saw += 1
            sd += ws
    print(f"  {sd}/{saw} = {100 * sd / saw:.4f}%")


if __name__ == "__main__":
    main(sys.argv[1])
