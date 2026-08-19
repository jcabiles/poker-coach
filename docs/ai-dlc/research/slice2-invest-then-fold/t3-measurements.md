# T3 measurements — every number the T3 comments cite

**Bottom line: the shipped river call damp is 0.06, which is not the derived
value. Minimum-defence arithmetic over the measured price distribution derives
about 0.46; two frozen went-to-showdown bands do not admit it, and the owner
ruled that conflict in the bands' favour on 2026-08-19. At 0.06 the folds that
are probability-1.000 by construction fall from 495 to 144, the headline node
mixes at P(call) 0.1821, pool went-to-showdown rises 0.94 points against a
3.78-point bound, and the river range still under-defends its obligation by 4.8
points.**

Regenerate any of this with the harness beside this file:

    cd backend && PYTHONPATH=. python -m tools.export_analytics \
        --hands 50000 --seed 20260817 \
        --lineup tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac \
        --out /tmp/sim50k-t3
    python docs/ai-dlc/research/slice2-invest-then-fold/t3_measure.py /tmp/sim50k-t3

`--lineup` is mandatory. The exporter default is alphabetical and comparable
with nothing.

## Why this file exists

T3's first round put every number behind untracked scripts. A figure measured
before the owner's band ruling and never re-measured — P(call) 0.691, which is
the undamped value — survived into a committed source comment, and all three
reviewers found it by reading rather than by running anything, because there was
nothing to run. Anything a source comment cites has to be somewhere a reader can
open.

## The four tips

| tip | damp | what it is |
|---|---|---|
| base | — | `f8dbb41`, T1 merged, ace-high's river call hard-zeroed |
| undamped | 1.00 | T3's predicate change with no damp — the mechanism at full strength |
| derived | 0.45 | the minimum-defence value, rounded; **both bands breach here** |
| **shipped** | **0.06** | what this pull request ships |

## Headline comparison

| statistic | base | undamped | derived 0.45 | **shipped 0.06** |
|---|---|---|---|---|
| folds that are probability-1.000 by construction | 495 | 150 | 151 | **144** |
| `diagnose.py`'s printed count (both buckets) | 495 | 250 | 321 | 444 |
| headline node, ace-high P(call) | 0.0000 | 0.6914 | 0.5196 | **0.1821** |
| headline node, air P(call) | 0.0000 | 0.0000 | 0.0000 | **0.0000** |
| invest-then-fold events | 1,084 | 798 | 880 | **1,015** |
| pool went-to-showdown | 54.1429% | 57.9385% | 56.9896% | **55.0865%** |
| river range continue vs MDF | 0.603 / 0.678 | 0.717 / 0.678 | 0.688 / 0.677 | **0.628 / 0.676** |
| ace-high realized win rate on its calls | — | 0.0739 | 0.0755 | **0.0800** |

## Acceptance criterion 1, reconciled rather than chosen between

The ticket's criterion 1 says the count of river air/ace-high folds facing a bet
at least the stack "should fall from 524 toward roughly 130 — the AIR-only
residual". Two different numbers get quoted against it and they measure different
things.

- **The ticket's literal statistic** is `diagnose.py`'s printed final line: FOLDS
  where the seat has committed at least 25bb, is being offered at least 5:1, is
  on the river with air or ace-high and no draw, and faces a bet at least its
  remaining stack. It reads 495 at the base and **444 at the shipped value**. It
  does not fall to 130 and **on its literal terms criterion 1 is not met.**
- **The property the criterion was written to capture** is determinism: the same
  filter restricted to AIR, the only bucket still hard-zeroed. It reads 495 at
  the base — every fold there was probability-1.000, because both buckets were
  zeroed — and **144 at the shipped value, which is the "roughly 130" the ticket
  predicted.** On this reading the criterion is met.
- **A third number, 380/382, is a different population** and should not be
  compared with either: it is every AIR decision at that node without the 25bb
  and pot-odds filters, and it exists only as the denominator showing air's
  P(call) is exactly 0.

The gap between the first two is the 300 ace-high folds still in the printed
count. They are not machine folds — they are outcomes of a decision that mixes at
P(call) 0.1821 — but the ticket's statistic cannot tell the difference, because it
counts folds rather than certainties. The ticket's own text assumed ace-high would
essentially stop folding, which is true only at a damp far above the one the
bands admit.

Note also, and this is the owner's to correct rather than mine: criterion 1's
"524" and "roughly 130" are pre-T1 figures. The post-T1 base this branch measures
against is 495.

## Raw output, all four tips


### base (T1, damp n/a)

```
export     : /tmp/claude-501/sim50k-t3-before
seed       : 20260817
engine sha : f8dbb41afce6765dff02c899c1b3ee6cc080389b
lineup     : tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac
             ^ the ratified lineup

=== 1. the determinism criterion, both statistics ===
  (a) `diagnose.py`'s printed count — river air/ace-high no-draw FOLDS
      in the invest-then-fold class facing a bet >= the remaining stack:
        ace_high|none    351
        air|none         144
        total            495
  (b) folds that are PROBABILITY-1.000 BY CONSTRUCTION — the same
      filter restricted to AIR, the only bucket still hard-zeroed:
          144
      The ace-high folds in (a) are outcomes of a mixed decision and
      are NOT determinism; before T3 every fold in (a) was in (b).

=== 2. the headline node — every decision, no raise offered ===
  ace_high|none  n=  823 fold=  823 call=    0 P(call)=0.0000
    maniac           n=  131 fold=  131 call=    0 P(call)=0.0000
    calling_station  n=  290 fold=  290 call=    0 P(call)=0.0000
    passive_fish     n=  196 fold=  196 call=    0 P(call)=0.0000
    lag              n=   70 fold=   70 call=    0 P(call)=0.0000
    tag              n=  123 fold=  123 call=    0 P(call)=0.0000
    nit              n=   13 fold=   13 call=    0 P(call)=0.0000
  air|none       n=  380 fold=  380 call=    0 P(call)=0.0000
    maniac           n=   84 fold=   84 call=    0 P(call)=0.0000
    calling_station  n=  178 fold=  178 call=    0 P(call)=0.0000
    passive_fish     n=   66 fold=   66 call=    0 P(call)=0.0000
    lag              n=   25 fold=   25 call=    0 P(call)=0.0000
    tag              n=   26 fold=   26 call=    0 P(call)=0.0000
    nit              n=    1 fold=    1 call=    0 P(call)=0.0000

=== 3. minimum-defence arithmetic (the derivation's input) ===
  river facing-chips decisions : 20245
  mean faced size f            : 0.5702 (ace-high subset)
  MDF = mean of 1/(1+f)        : 0.6756
  range continue (call+raise)  : 12205/20245 = 0.6029
  shortfall against MDF        : +0.0727
  bucket                      n   share  continue
  middle_pair|none         5890   29.1%    0.7411
  ace_high|none            4097   20.2%    0.0605
  monster|none             3629   17.9%    1.0000
  air|none                 2680   13.2%    0.0694
  top_pair|none            2009    9.9%    0.9238
  two_pair_plus|none       1454    7.2%    0.9911
  overpair_tptk|none        486    2.4%    0.9877

=== 4. price faced, and what the calls actually win ===
  faced size f    : p10 0.248  median 0.500  p90 1.000  mean 0.570
  required equity : p10 0.166  median 0.250  mean 0.248
  faced band          n  calls   P(call)
  f<=0.25           455      0    0.0000
  0.25<f<=0.50     1889      0    0.0000
  0.50<f<=0.85     1116      0    0.0000
  f>0.85            637      0    0.0000

=== 5. multiway (opponent count rebuilt from the decisions stream) ===
  ace_high|none  heads-up  n= 2659 P(call)=0.0000
  ace_high|none  multiway  n= 1438 P(call)=0.0000
  air|none       heads-up  n= 1672 P(call)=0.0000
  air|none       multiway  n= 1008 P(call)=0.0000

=== 6. pool went-to-showdown ===
  58365/107798 = 54.1429%
```

### undamped (damp 1.00)

```
export     : /tmp/claude-501/sim50k-t3-after
seed       : 20260817
engine sha : f8dbb41afce6765dff02c899c1b3ee6cc080389b
lineup     : tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac
             ^ the ratified lineup

=== 1. the determinism criterion, both statistics ===
  (a) `diagnose.py`'s printed count — river air/ace-high no-draw FOLDS
      in the invest-then-fold class facing a bet >= the remaining stack:
        ace_high|none    100
        air|none         150
        total            250
  (b) folds that are PROBABILITY-1.000 BY CONSTRUCTION — the same
      filter restricted to AIR, the only bucket still hard-zeroed:
          150
      The ace-high folds in (a) are outcomes of a mixed decision and
      are NOT determinism; before T3 every fold in (a) was in (b).

=== 2. the headline node — every decision, no raise offered ===
  ace_high|none  n=  794 fold=  245 call=  549 P(call)=0.6914
    maniac           n=  124 fold=   38 call=   86 P(call)=0.6935
    calling_station  n=  280 fold=   26 call=  254 P(call)=0.9071
    passive_fish     n=  189 fold=   93 call=   96 P(call)=0.5079
    lag              n=   61 fold=   27 call=   34 P(call)=0.5574
    tag              n=  128 fold=   52 call=   76 P(call)=0.5938
    nit              n=   12 fold=    9 call=    3 P(call)=0.2500
  air|none       n=  355 fold=  355 call=    0 P(call)=0.0000
    maniac           n=   84 fold=   84 call=    0 P(call)=0.0000
    calling_station  n=  165 fold=  165 call=    0 P(call)=0.0000
    passive_fish     n=   59 fold=   59 call=    0 P(call)=0.0000
    lag              n=   21 fold=   21 call=    0 P(call)=0.0000
    tag              n=   25 fold=   25 call=    0 P(call)=0.0000
    nit              n=    1 fold=    1 call=    0 P(call)=0.0000

=== 3. minimum-defence arithmetic (the derivation's input) ===
  river facing-chips decisions : 19854
  mean faced size f            : 0.5573 (ace-high subset)
  MDF = mean of 1/(1+f)        : 0.6780
  range continue (call+raise)  : 14243/19854 = 0.7174
  shortfall against MDF        : -0.0393
  bucket                      n   share  continue
  middle_pair|none         5778   29.1%    0.7470
  ace_high|none            4088   20.6%    0.6309
  monster|none             3482   17.5%    1.0000
  air|none                 2653   13.4%    0.0663
  top_pair|none            1988   10.0%    0.9235
  two_pair_plus|none       1394    7.0%    0.9950
  overpair_tptk|none        471    2.4%    0.9915

=== 4. price faced, and what the calls actually win ===
  faced size f    : p10 0.248  median 0.500  p90 1.000  mean 0.557
  required equity : p10 0.166  median 0.250  mean 0.245
  faced band          n  calls   P(call)
  f<=0.25           511    365    0.7143
  0.25<f<=0.50     1869   1203    0.6437
  0.50<f<=0.85     1092    582    0.5330
  f>0.85            616    341    0.5536
  calls made 2491; mean required equity of those calls 0.2377; realized win rate 0.0739 (184/2491)
    f<=0.25        calls   365  win rate 0.0219
    0.25<f<=0.50   calls  1203  win rate 0.0515
    0.50<f<=0.85   calls   582  win rate 0.0979
    f>0.85         calls   341  win rate 0.1672

=== 5. multiway (opponent count rebuilt from the decisions stream) ===
  ace_high|none  heads-up  n= 2475 P(call)=0.6097
  ace_high|none  multiway  n= 1613 P(call)=0.6088
  air|none       heads-up  n= 1571 P(call)=0.0000
  air|none       multiway  n= 1082 P(call)=0.0000

=== 6. pool went-to-showdown ===
  62376/107659 = 57.9385%
```

### derived (damp 0.45)

```
export     : /tmp/claude-501/sim50k-t3-damp
seed       : 20260817
engine sha : 65eab4575a4694564f002a7bc5ff3fc17cb5e800
lineup     : tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac
             ^ the ratified lineup

=== 1. the determinism criterion, both statistics ===
  (a) `diagnose.py`'s printed count — river air/ace-high no-draw FOLDS
      in the invest-then-fold class facing a bet >= the remaining stack:
        ace_high|none    170
        air|none         151
        total            321
  (b) folds that are PROBABILITY-1.000 BY CONSTRUCTION — the same
      filter restricted to AIR, the only bucket still hard-zeroed:
          151
      The ace-high folds in (a) are outcomes of a mixed decision and
      are NOT determinism; before T3 every fold in (a) was in (b).

=== 2. the headline node — every decision, no raise offered ===
  ace_high|none  n=  816 fold=  392 call=  424 P(call)=0.5196
    maniac           n=  128 fold=   76 call=   52 P(call)=0.4062
    calling_station  n=  291 fold=   65 call=  226 P(call)=0.7766
    passive_fish     n=  186 fold=  120 call=   66 P(call)=0.3548
    lag              n=   68 fold=   42 call=   26 P(call)=0.3824
    tag              n=  131 fold=   79 call=   52 P(call)=0.3969
    nit              n=   12 fold=   10 call=    2 P(call)=0.1667
  air|none       n=  362 fold=  362 call=    0 P(call)=0.0000
    maniac           n=   82 fold=   82 call=    0 P(call)=0.0000
    calling_station  n=  175 fold=  175 call=    0 P(call)=0.0000
    passive_fish     n=   61 fold=   61 call=    0 P(call)=0.0000
    lag              n=   18 fold=   18 call=    0 P(call)=0.0000
    tag              n=   25 fold=   25 call=    0 P(call)=0.0000
    nit              n=    1 fold=    1 call=    0 P(call)=0.0000

=== 3. minimum-defence arithmetic (the derivation's input) ===
  river facing-chips decisions : 19949
  mean faced size f            : 0.5592 (ace-high subset)
  MDF = mean of 1/(1+f)        : 0.6768
  range continue (call+raise)  : 13720/19949 = 0.6878
  shortfall against MDF        : -0.0110
  bucket                      n   share  continue
  middle_pair|none         5852   29.3%    0.7502
  ace_high|none            4100   20.6%    0.4824
  monster|none             3443   17.3%    1.0000
  air|none                 2642   13.2%    0.0659
  top_pair|none            2013   10.1%    0.9215
  two_pair_plus|none       1413    7.1%    0.9908
  overpair_tptk|none        486    2.4%    0.9877

=== 4. price faced, and what the calls actually win ===
  faced size f    : p10 0.248  median 0.500  p90 1.000  mean 0.559
  required equity : p10 0.166  median 0.250  mean 0.245
  faced band          n  calls   P(call)
  f<=0.25           505    263    0.5208
  0.25<f<=0.50     1899    892    0.4697
  0.50<f<=0.85     1068    433    0.4054
  f>0.85            628    253    0.4029
  calls made 1841; mean required equity of those calls 0.2374; realized win rate 0.0755 (139/1841)
    f<=0.25        calls   263  win rate 0.0304
    0.25<f<=0.50   calls   892  win rate 0.0516
    0.50<f<=0.85   calls   433  win rate 0.0947
    f>0.85         calls   253  win rate 0.1739

=== 5. multiway (opponent count rebuilt from the decisions stream) ===
  ace_high|none  heads-up  n= 2527 P(call)=0.4448
  ace_high|none  multiway  n= 1573 P(call)=0.4558
  air|none       heads-up  n= 1572 P(call)=0.0000
  air|none       multiway  n= 1070 P(call)=0.0000

=== 6. pool went-to-showdown ===
  61355/107660 = 56.9896%
```

### SHIPPED (damp 0.06)

```
export     : /tmp/claude-501/sim50k-t3-confirm
seed       : 20260817
engine sha : e238e47d78492e50d309c36c941b39a12d47efe5
lineup     : tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac
             ^ the ratified lineup

=== 1. the determinism criterion, both statistics ===
  (a) `diagnose.py`'s printed count — river air/ace-high no-draw FOLDS
      in the invest-then-fold class facing a bet >= the remaining stack:
        ace_high|none    300
        air|none         144
        total            444
  (b) folds that are PROBABILITY-1.000 BY CONSTRUCTION — the same
      filter restricted to AIR, the only bucket still hard-zeroed:
          144
      The ace-high folds in (a) are outcomes of a mixed decision and
      are NOT determinism; before T3 every fold in (a) was in (b).

=== 2. the headline node — every decision, no raise offered ===
  ace_high|none  n=  829 fold=  678 call=  151 P(call)=0.1821
    maniac           n=  132 fold=  118 call=   14 P(call)=0.1061
    calling_station  n=  295 fold=  190 call=  105 P(call)=0.3559
    passive_fish     n=  198 fold=  184 call=   14 P(call)=0.0707
    lag              n=   70 fold=   65 call=    5 P(call)=0.0714
    tag              n=  121 fold=  109 call=   12 P(call)=0.0992
    nit              n=   13 fold=   12 call=    1 P(call)=0.0769
  air|none       n=  382 fold=  382 call=    0 P(call)=0.0000
    maniac           n=   83 fold=   83 call=    0 P(call)=0.0000
    calling_station  n=  185 fold=  185 call=    0 P(call)=0.0000
    passive_fish     n=   64 fold=   64 call=    0 P(call)=0.0000
    lag              n=   22 fold=   22 call=    0 P(call)=0.0000
    tag              n=   27 fold=   27 call=    0 P(call)=0.0000
    nit              n=    1 fold=    1 call=    0 P(call)=0.0000

=== 3. minimum-defence arithmetic (the derivation's input) ===
  river facing-chips decisions : 20135
  mean faced size f            : 0.5612 (ace-high subset)
  MDF = mean of 1/(1+f)        : 0.6762
  range continue (call+raise)  : 12648/20135 = 0.6282
  shortfall against MDF        : +0.0480
  bucket                      n   share  continue
  middle_pair|none         5848   29.0%    0.7425
  ace_high|none            4123   20.5%    0.1940
  monster|none             3561   17.7%    1.0000
  air|none                 2669   13.3%    0.0671
  top_pair|none            2028   10.1%    0.9255
  two_pair_plus|none       1421    7.1%    0.9916
  overpair_tptk|none        485    2.4%    0.9897

=== 4. price faced, and what the calls actually win ===
  faced size f    : p10 0.248  median 0.500  p90 1.000  mean 0.561
  required equity : p10 0.166  median 0.250  mean 0.246
  faced band          n  calls   P(call)
  f<=0.25           476     83    0.1744
  0.25<f<=0.50     1936    275    0.1420
  0.50<f<=0.85     1102    137    0.1243
  f>0.85            609     80    0.1314
  calls made 575; mean required equity of those calls 0.2380; realized win rate 0.0800 (46/575)
    f<=0.25        calls    83  win rate 0.0361
    0.25<f<=0.50   calls   275  win rate 0.0436
    0.50<f<=0.85   calls   137  win rate 0.1022
    f>0.85         calls    80  win rate 0.2125

=== 5. multiway (opponent count rebuilt from the decisions stream) ===
  ace_high|none  heads-up  n= 2636 P(call)=0.1415
  ace_high|none  multiway  n= 1487 P(call)=0.1358
  air|none       heads-up  n= 1650 P(call)=0.0000
  air|none       multiway  n= 1019 P(call)=0.0000

=== 6. pool went-to-showdown ===
  59397/107825 = 55.0865%
```
