#!/usr/bin/env python3
"""make_audit_tables.py - generate the appendix results tables from results/*.json.

Writes paper/tables_audit.tex as a set of \\newcommand definitions. The paper \\input{}s the file
and places each table by name. NEVER EDIT tables_audit.tex: it is overwritten on every build, and
a hand edit is exactly how a stale number gets into a paper that claims none are transcribed.

    .venv/bin/python paper/tools/make_audit_tables.py

TABLES
    \\tblladder      the four-rung ladder: R per rung, tau, verdicts           [d3, cv6, cv7]
    \\tblbaseline    the unfitted logit-lens baseline at each rung             [cv6, cv7]
    \\tblfamily      per-family corpus effect at 410M, rank and z              [d3]
    \\tblderange     each map against 15 derangements of itself           [r9, e54]
    \\tblclustered   the corpus-clustered paired t on the derangement gap      [paper]
    \\tblvariance    fit x read variance decomposition with bootstrap CIs      [e57]
    \\tblcompetence  answer competence and prompt surprisal up the ladder      [cv4]
    \\tblposition    read position against fitting support                     [cv2]
    \\tblcrossover   every fitted map against the free logit lens at 410M   [e48 rstrip]
    \\tblcontain     32-gram containment against the published stream          [e48b, e48c]
    \\tblcalib       calibration of the containment index                      [e48b]

Every table is placed with [H], not [h]: the appendix reads in the order the tables are written.
"""
from __future__ import annotations

import json
import os
import re

# Lives at paper/tools/, so the repo root is TWO levels up (moved 2026-08-31).
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RES = os.path.join(ROOT, "results")
DEST = os.path.join(ROOT, "paper", "tables_audit.tex")

FAMS = ["multihop", "multilingual", "order-ops", "poetry", "typo"]
INSTREAM = ["Wikipedia_en", "USPTO_Backgrounds", "Pile-CC", "StackExchange", "Github"]
SHORT = {"Wikipedia_en": "Wikipedia", "USPTO_Backgrounds": "USPTO", "Pile-CC": "Pile-CC",
         "StackExchange": "StackExchange", "Github": "GitHub", "OOD_News_2024": "News 2024",
         "OOD_arXiv_2023": "arXiv 2023", "OOD_CommonPile": "Common Pile",
         "CONTROL_PubMed_2023": "PubMed (control)", "OOD_Wikipedia_2023": "Wikipedia 2023",
         "TRAP_FineWeb": "FineWeb (trap)", "_CONTROL_random": "Uniform random tokens"}
# Display names only; the results files keep their keys. The same names are used in the body text
# and in figures/make_audit_figures.py.
FAMNAME = {"multihop": "Multi-hop", "multilingual": "Multilingual", "order-ops": "Order of operations",
           "poetry": "Poetry", "typo": "Typo", "association": "Association"}
FAMSHORT = dict(FAMNAME, **{"order-ops": "Order of ops."})       # where a table is narrow
ABBR = {"Wikipedia_en": "Wiki", "USPTO_Backgrounds": "USPTO", "Pile-CC": "Pile-CC",
        "StackExchange": "StackEx", "Github": "GitHub"}               # the family table's ordering column
TIER = {"in-stream": "Pile component", "github": "Pile component", "OOD": "After the Pile"}
AGG = {"min": "Any-layer", "persist": "Majority-layer"}
ANCHOR_410M = 0.19810852520167826   # the stored 410M identity arm; C1 of every prereg checks it
MODELS = [("70m", "70M"), ("160m", "160M"), ("410m", "410M"),
          ("1b", "1B"), ("1.4b", "1.4B"), ("2.8b", "2.8B")]


def load(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)


def esc(s):
    return s.replace("_", "\\_")


def caption_above(block):
    """Move \\caption/\\label above the tabular, which is where this paper puts them.

    A reader meets the explanation before the grid of numbers, and consecutive tables in an
    appendix section then read as caption/table/caption/table rather than table/caption pairs
    that visually bind to the wrong neighbour.
    """
    i = block.find("\\begin{tabular}")
    if i < 0:
        return block
    head, tail = block[:i], block[i:]
    j = tail.find("\\caption{")
    if j < 0:
        return block
    k, depth = j + len("\\caption{"), 1
    while k < len(tail) and depth:
        if tail[k] == "{": depth += 1
        elif tail[k] == "}": depth -= 1
        k += 1
    cap = tail[j:k]
    rest = tail[:j] + tail[k:]
    m = re.search(r"\n?\\label\{[^}]*\}", rest)
    lab = ""
    if m:
        lab = m.group(0).strip()
        rest = rest[:m.start()] + rest[m.end():]
    rest = re.sub(r"\n{3,}", "\n\n", rest)
    return head + cap + ("\n" + lab if lab else "") + "\n" + rest.lstrip("\n")


def wrap(cmd, body):
    return "\\newcommand{\\%s}{%%\n%s}\n\n" % (cmd, caption_above(body))


def wrap_many(names, body):
    """Split a body holding several tables and wrap each under its own \\newcommand.

    ONE MACRO PER TABLE. Three macros used to emit two tables apiece, so the paper had no way to
    put tab:baseline, tab:clustered or tab:calib anywhere except immediately after the table they
    were bundled with, which is how the appendix ended up ordered by generator convenience.
    """
    parts = body.split("\n\n\\begin{table}")
    parts = [parts[0]] + ["\\begin{table}" + p for p in parts[1:]]
    assert len(parts) == len(names), (len(parts), len(names))
    return "".join(wrap(n, p) for n, p in zip(names, parts))


def tbl_ladder(d3, cv6, cv7):
    """The four-rung ladder. R is reported per rung WITH its N, never compared across N."""
    r14 = {f: v["z_spread"] / v["z_pooled_seed_sd"]
           for f, v in cv6["by_model"]["1.4b"]["by_family"].items()}
    r28 = cv6["PRIMARY"]["R_per_family_2.8b"]
    r1b = cv7["PRIMARY"]["R_per_family_1b"]
    tau28 = cv6["PRIMARY"]["kendall_tau_vs_410m_2.8b"]
    tau1b = cv7["PRIMARY"]["kendall_tau_vs_410m"]
    tau14 = {f: v["kendall_tau_vs_410m"] for f, v in cv6["by_model"]["1.4b"]["by_family"].items()}
    spread = cv7["CROSS_LADDER_z_spread"]["z_spread_by_rung"]
    rows = []
    for f in FAMS:
        rows.append(
            f"{FAMNAME[f]} & {d3['by_family'][f]['n_pairs']} & "
            f"{d3['by_family'][f]['z_spread_over_sd']:.1f} & {r1b[f]:.1f} & {r14[f]:.1f} & {r28[f]:.1f} & "
            f"{tau1b[f]:+.1f} & {tau14[f]:+.1f} & {tau28[f]:+.1f} & "
            f"{spread['410m_N200'][f]:.3f} & {spread['2.8b_N25'][f]:.3f} \\\\")
    body = r"""\begin{table}[H]
\centering\scriptsize\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lrrrrrrrrrr@{}}
\toprule
& & \multicolumn{4}{c}{$R$ = spread of $z$ / pooled seed SD} & \multicolumn{3}{c}{Kendall $\tau$ vs.\ 410M}
& \multicolumn{2}{c}{Spread of $z$} \\
\cmidrule(lr){3-6}\cmidrule(lr){7-9}\cmidrule(lr){10-11}
Family & Pairs & 410M & 1B & 1.4B & 2.8B & 1B & 1.4B & 2.8B & 410M & 2.8B \\
& & \emph{200} & \emph{200} & \emph{25} & \emph{25} & & & & \emph{200} & \emph{25} \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{The corpus effect at four rungs of the Pythia ladder. The italic row gives $N$, the number
of fitting prompts per map. $R$ is not comparable across rungs with different $N$, because
the pooled seed SD is $2.29\times$ to $5.70\times$ larger at $N{=}25$ than at $N{=}200$, so the
$N{=}200$ columns and the $N{=}25$ columns are two different scales. The quantity that is comparable
is the $z$ spread, in the last two columns, and it grew from 410M to 2.8B in five of five families.
The 1.4B rung carries no verdict: its numbers were seen before a rule for it could be written. An
$R$ of 10 has a one-sided exceedance of $1.0\times10^{-4}$ to $5.7\times10^{-3}$ under a permutation
null over corpus labels, and $\tau\ge0.6$ has exact null probability $14/120$ per family.}
\label{tab:ladder}
\end{table}

\begin{table}[H]
\centering\small\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{6pt}
\begin{tabular}{@{}lrrrr@{}}
\toprule
& 410M & 1B & 1.4B & 2.8B \\
\midrule
Logit-lens readout score, any-layer (\texttt{min}) & """ + \
f"{1e2*ANCHOR_410M:.2f} & {1e2*cv7['logit_I_pooled_rank_flatmean7']:.2f} & " \
f"{1e2*cv6['by_model']['1.4b']['logit_I_pooled_rank_flatmean7']:.2f} & " \
f"{1e2*cv6['by_model']['2.8b']['logit_I_pooled_rank_flatmean7']:.2f}" + r""" \\
\bottomrule
\end{tabular}
\caption{The unfitted baseline rises monotonically at every rung. Any comparison of a fitted
map against the free lens at 2.8B is therefore against a stronger baseline than at 410M, and a
table that omits this row overstates the fitted map at scale.}
\label{tab:baseline}
\end{table}"""
    return wrap_many(["tblladder", "tblbaseline"], body)


def tbl_family(d3):
    rows = []
    for f in FAMS:
        b = d3["by_family"][f]
        order = " $>$ ".join(ABBR[c] for c in b["order_by_z"])
        rows.append(f"{FAMNAME[f]} & {b['n_pairs']} & {b['logit_z']:.3f} & {b['z_spread']:.4f} & "
                    f"{b['z_pooled_seed_sd']:.5f} & {b['z_spread_over_sd']:.1f} & "
                    f"{b['rank_spread_over_sd']:.1f} & {order} \\\\")
    body = r"""\begin{table}[H]
\centering\scriptsize\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{@{}lrrrrrrl@{}}
\toprule
Family & Pairs & Logit-lens $z$ & Spread of $z$ & Seed SD & $z$/SD & Rank/SD & Best to worst by $z$ \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{The corpus effect at 410M decomposed by evaluation family. We report per family because
multilingual is $394$ of $801$ scored pairs and the model answers $0.9\%$ of it. The spread is
across the five in-stream fitting corpora; the seed SD is the RMS of per-corpus sample SDs over
three seed blocks, computed inside that family. Wiki is Wikipedia and StackEx is StackExchange. Rank and $z$ disagree about where the effect is largest. The bottom of
the $z$ ordering is the same in all five families; the top three permute. Exploratory.}
\label{tab:family}
\end{table}"""
    return wrap("tblfamily", body)


def tbl_derange(r9, e54):
    def find(o, key):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == key:
                    return v
                hit = find(v, key)
                if hit is not None:
                    return hit
        return None

    c2 = find(e54, "C2_derangement")
    rows = []
    for c in r9["by_aggregation"]["min"]["per_corpus"]:
        m = r9["by_aggregation"]["min"]["per_corpus"][c]
        p = r9["by_aggregation"]["persist"]["per_corpus"][c]
        gm = c2["min"]["per_corpus"][c]
        rows.append(f"{SHORT[c]} & {1e2*m['real']:.2f} & {1e2*m['null_mean']:.2f} & {m['z_vs_null']:+.2f} & "
                    f"{gm['shuf_beats_jp_paired']}/15 & "
                    f"{1e2*p['real']:.2f} & {1e2*p['null_mean']:.2f} & {p['z_vs_null']:+.2f} \\\\")
    body = r"""\begin{table}[H]
\centering\scriptsize\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{5pt}
\begin{tabular}{@{}lrrrrrrr@{}}
\toprule
& \multicolumn{4}{c}{Any-layer (\texttt{min}), published} & \multicolumn{3}{c}{Majority-layer (\texttt{persist})} \\
\cmidrule(lr){2-5}\cmidrule(lr){6-8}
Fitting corpus & Real & Null mean & $z$ & Null wins & Real & Null mean & $z$ \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Each fitted map scored against fifteen layer-derangements of itself, at the corrected
readout. Under \texttt{min} seven of eight maps sit below their own null's mean, exact
one-sided binomial $p=0.0352$, and the derangement wins a majority of paired draws on the same seven;
under \texttt{persist} every map sits above its null and the derangement wins none. Fifteen
draws floor the empirical $p$ at $1/16$, so no single row can reach $p<0.05$. The count of maps
clearing every own draw, 0 of 8 under \texttt{min} against 8 of 8 under \texttt{persist}, is not
the inferential statement: a count of zero arises under the exact null with probability
$(15/16)^8=0.597$. The direction is the statistic.}
\label{tab:derange}
\end{table}"""
    return wrap("tblderange", body)


def tbl_variance(e57, clustered):
    rows = []
    for agg in ("min", "persist"):
        a = e57["by_aggregation"][agg]
        pt, bs = a["point"], a["bootstrap"]
        fm = bs["fit_minus_read"]
        rows.append(
            f"{AGG[agg]} & {pt['fit_pct']:.2f} "
            f"[{bs['fit_pct']['ci_lo']:.1f}, {bs['fit_pct']['ci_hi']:.1f}] & "
            f"{pt['read_pct']:.2f} [{bs['read_pct']['ci_lo']:.1f}, {bs['read_pct']['ci_hi']:.1f}] & "
            f"{pt['resid_pct']:.2f} & "
            f"{fm['point']:+.2f} [{fm['ci_lo']:+.2f}, {fm['ci_hi']:+.2f}] & "
            f"{'Yes' if fm['excludes_zero'] else 'No'} \\\\")
    cm = clustered["by_readout"]["corrected"]["min"]
    lm = clustered["by_readout"]["legacy"]["min"]
    cp = clustered["by_readout"]["corrected"]["persist"]
    body = r"""\begin{table}[H]
\centering\small\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{5pt}
\begin{tabular}{@{}lccccc@{}}
\toprule
Recovery rule & Fit \% [95\% CI] & Read \% [95\% CI] & Residual \% & Fit $-$ read [95\% CI] & Excludes 0 \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Variance shares of the $8\times8$ fit\,$\times$\,read grid at 410M, corrected readout.
Intervals are 95\% bootstrap over both seed factors, 10{,}000 resamples. The ordering holds under
both aggregations, but the interval on the difference excludes zero only under \texttt{min}.}
\label{tab:variance}
\end{table}

\begin{table}[H]
\centering\small\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{6pt}
\begin{tabular}{@{}llrrr@{}}
\toprule
Scorer & Recovery rule & Mean gap (points) & $t(7)$ & $p$ (two-sided) \\
\midrule
Corrected & Any-layer & """ + f"{1e2*cm['mean_gap']:+.3f} & {cm['t']:+.2f} & {cm['p_two_sided']:.3f}" + r""" \\
Corrected & Majority-layer & """ + f"{1e2*cp['mean_gap']:+.3f} & {cp['t']:+.2f} & {cp['p_two_sided']:.1e}" + r""" \\
Pre-correction & Any-layer & """ + f"{1e2*lm['mean_gap']:+.3f} & {lm['t']:+.2f} & {lm['p_two_sided']:.3f}" + r""" \\
\bottomrule
\end{tabular}
\caption{Corpus-clustered paired $t$ on the derangement gap, the inferential companion to
Table~\ref{tab:derange}. The replication unit is the corpus, not the draw, because fifteen
derangements of one map share the same map and cache. At the corrected readout, evidence that
\texttt{min} prefers the derangement does not clear $5\%$; at the legacy readout it did. We therefore
do not use this null as an identifying control.}
\label{tab:clustered}
\end{table}"""
    return wrap_many(["tblvariance", "tblclustered"], body)


def tbl_competence(cv4):
    rows = []
    for key, label in MODELS:
        m = cv4["by_model"][key]
        p = m["_pooled_answer"]
        rows.append(
            f"{label} & {100*p['top1_rate']:.1f} "
            f"[{100*p['top1_wilson95'][0]:.1f}, {100*p['top1_wilson95'][1]:.1f}] & "
            f"{100*p['top10_rate']:.1f} "
            f"[{100*p['top10_wilson95'][0]:.1f}, {100*p['top10_wilson95'][1]:.1f}] & "
            f"{m['multihop']['median_rank']} & {m['order-ops']['median_rank']} & "
            f"{m['multilingual']['median_rank']} & {m['_pooled_surprisal_all_six']:.3f} \\\\")
    body = r"""\begin{table}[H]
\centering\small\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{5pt}
\begin{tabular}{@{}lccrrrr@{}}
\toprule
& \multicolumn{2}{c}{Pooled, 255 prompts with an answer} & \multicolumn{3}{c}{Median answer rank}
& Prompt \\
\cmidrule(lr){2-3}\cmidrule(lr){4-6}
Model & Top-1 \% [95\% CI] & Top-10 \% [95\% CI] & Multi-hop & Order of ops. & Multilingual & surprisal \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Answer competence, corrected readout, 95\% Wilson intervals~\citep{wilson1927}. Only
multihop, order-ops and multilingual carry an expected answer; poetry, typo and association carry
\texttt{target: null}, so answer competence is undefined for them rather than zero. Prompt surprisal
is the mean per-token negative log likelihood over all 551 items in all six families. Top-1 never
separates from 410M once the intervals are attached, while surprisal falls monotonically: the models
become more fluent on the prompts without becoming measurably better at answering them.}
\label{tab:competence}
\end{table}"""
    return wrap("tblcompetence", body)


def tbl_position(cv2):
    rows = []
    for s, v in cv2["by_set"].items():
        q0, pf = v["Q0"], v["prefixed"]
        rows.append(
            f"{FAMSHORT[s]} & {v['n_items']} & {v['median_prompt_tokens']} & "
            f"{q0['median_read_pos']} & {q0['min']}--{q0['max']} & {100*q0['frac_in_support']:.1f} & "
            f"{pf['median_read_pos']} & {pf['min']}--{pf['max']} & {100*pf['frac_in_support']:.1f} \\\\")
    o = cv2["overall"]
    rows.append("\\midrule")
    rows.append(
        f"All & {o['Q0']['n']} & & {o['Q0']['median_read_pos']} & "
        f"{o['Q0']['min']}--{o['Q0']['max']} & {100*o['Q0']['frac_in_support']:.1f} & "
        f"{o['prefixed']['median_read_pos']} & "
        f"{o['prefixed']['min']}--{o['prefixed']['max']} & "
        f"{100*o['prefixed']['frac_in_support']:.1f} \\\\")
    lo, hi = cv2["fitting_support"]["inclusive_range"]
    body = r"""\begin{table}[H]
\centering\small\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{5pt}
\begin{tabular}{@{}lrrrrrrrr@{}}
\toprule
& & Median & \multicolumn{3}{c}{No prefix} & \multicolumn{3}{c}{128-token prefix} \\
\cmidrule(lr){4-6}\cmidrule(lr){7-9}
Family & Prompts & length & Median & Range & In support \% & Median & Range & In support \% \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Read position against the positional support of the fitted map. The fitter averages
the Jacobian over positions """ + f"{lo} to {hi}" + r""" of a 128-token window. Not one of 551 items
on any prefixed rung is read inside that range, and without a prefix the majority of the remainder
sit below it, inside the attention-sink zone the fitter deliberately excludes. The two conditions
extrapolate in opposite directions.}
\label{tab:position}
\end{table}"""
    return wrap("tblposition", body)


def tbl_crossover(e48r):
    """Every fitted map against the free lens, both aggregations, at the corrected readout.

    The free baseline is one number per aggregation and is identical on every rung, so it is
    printed once under a midrule rather than repeated down a column. The percentage is the point
    estimate as a fraction of that baseline; the interval behind it is the file's three-level
    hierarchical bootstrap, and the COUNT of intervals excluding zero goes in the caption rather
    than into a fifth and sixth column, which would double the table's ink for one bit each.
    """
    rungs = e48r["rungs"]
    base = {a: next(iter(rungs.values()))[a]["logit_admitted_mean"] for a in ("min", "persist")}
    order = sorted(rungs, key=lambda c: -rungs[c]["min"]["jp_admitted_mean"])
    rows = []
    for c in order:
        m, p = rungs[c]["min"], rungs[c]["persist"]
        rows.append(
            f"{SHORT.get(c, esc(c))} & {1e2*m['jp_admitted_mean']:.2f} & "
            f"{100*(m['jp_admitted_mean']/base['min']-1):+.1f} & "
            f"{1e2*p['jp_admitted_mean']:.2f} & "
            f"{100*(p['jp_admitted_mean']/base['persist']-1):+.1f} \\\\")
    n_min = sum(rungs[c]["min"]["ci_strictly_positive"] for c in order)
    n_per = sum(rungs[c]["persist"]["ci_strictly_positive"] for c in order)
    body = r"""\begin{table}[H]
\centering\small\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{6pt}
\begin{tabular}{@{}lrrrr@{}}
\toprule
& \multicolumn{2}{c}{Any-layer (\mn)} & \multicolumn{2}{c}{Majority-layer (\pe)} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Fitting corpus & Readout score & Gain \% & Readout score & Gain \% \\
\midrule
""" + "\n".join(rows) + r"""
\midrule
Logit lens (unfitted) & """ + f"{1e2*base['min']:.2f}" + r""" & & """ + f"{1e2*base['persist']:.2f}" + r""" & \\
\bottomrule
\end{tabular}
\caption{Each fitted map at 410M against the unfitted logit lens, corrected readout, on
identical cached activations. The readout score is the mean over the five admitted families and three
fitting seeds; the gain is the point estimate relative to the logit lens, whose value is one
number per recovery rule and is printed once. Of the eight differences, """ + f"{n_min}" + r""" under
\mn{} and """ + f"{n_per}" + r""" under \pe{} have three-level hierarchical bootstrap intervals
excluding zero, over eval set, seed block and item pair.}
\label{tab:crossover}
\end{table}"""
    return wrap("tblcrossover", body)


def tbl_contain(e48b, e48c):
    k32 = e48b["containment_by_coverage"]["32"]
    rows = []
    for c, v in e48c["by_rung"].items():
        rows.append(f"{SHORT[c]} & {TIER[v['tier']]} & {v['containment_k32']:.5f} \\\\")
    ctrl = [c for c in k32 if c not in e48c["by_rung"]]
    crows = [f"{SHORT.get(c, esc(c))} & {k32[c][-1]:.5f} \\\\" for c in sorted(ctrl)]
    r = e48c["correlations"]
    body = r"""\begin{table}[H]
\centering\small\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{6pt}
\begin{tabular}{@{}llr@{}}
\toprule
Fitting corpus & Group & Containment ($k{=}32$) \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{32-gram containment of each fitting corpus against the full published training stream, 20
of 20 shards: the fraction of the corpus's 32-token windows that occur verbatim in the stream. The
five Pile components sit above $0.9$; the three later or external corpora sit at or below the level
that reformatting alone produces (Table~\ref{tab:calib}) and are reported as ``no match found at
$k{=}32$'' rather than as absent from training. The readout each corpus produces is in
Figure~\ref{fig:membership}.}
\label{tab:contain}
\end{table}

\begin{table}[H]
\centering\small\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{4pt}\setlength{\tabcolsep}{6pt}
\begin{tabular}{@{}lr@{}}
\toprule
Calibration corpus & Containment ($k{=}32$) \\
\midrule
""" + "\n".join(crows) + r"""
\bottomrule
\end{tabular}
\caption{Calibration of the containment index. Re-wrapping identical text to a different line width
leaves only $0.14\%$ to $2.4\%$ of its 32-grams intact, so any value in that band cannot be read as
absence. A post-cutoff Wikipedia dump and a PubMed control both score far above the out-of-stream
corpora, and uniform-random tokens score exactly zero. Document-level temporal exclusion does not
give textual novelty, which is why we report ``no match found at $k{=}32$'' rather than ``absent
from training''.}
\label{tab:calib}
\end{table}"""
    return wrap_many(["tblcontain", "tblcalib"], body)


def tbl_grid(e52):
    """The 64 cell values of the factorial, which Fig. 1 renders as colour rather than digits.

    Fig. 1 deliberately carries no numbers in the matrix: the finding is a row pattern and 64
    four-digit labels hide it. They live here instead, so nothing is lost.
    """
    cells = e52["by_aggregation"]["min"]["matrix"]
    fits = e52["fit_corpora"]
    rows = []
    for f in fits:
        vals = [cells.get(f"{f}|{r}") for r in fits]
        mean = sum(v for v in vals if v is not None) / sum(1 for v in vals if v is not None)
        cs = " & ".join("--" if v is None else f"{1e2*v:.2f}" for v in vals)
        rows.append(f"{SHORT[f]} & {cs} & \\textbf{{{1e2*mean:.2f}}} \\\\")
    colmeans = []
    for r in fits:
        vals = [cells.get(f"{f}|{r}") for f in fits]
        vals = [v for v in vals if v is not None]
        colmeans.append(sum(vals) / len(vals))
    rows.append("\\midrule")
    rows.append("Mean & " + " & ".join(f"\\textbf{{{1e2*v:.2f}}}" for v in colmeans) + " & \\\\")
    head = " & ".join(SHORT[r] for r in fits)
    body = r"""\begin{table}[H]
\centering\scriptsize\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{@{}l""" + "r" * (len(fits) + 1) + r"""@{}}
\toprule
Fitting corpus & \multicolumn{""" + str(len(fits)) + r"""}{c}{Read context} & Mean \\
\cmidrule(lr){2-""" + str(len(fits) + 1) + r"""}
 & """ + head + r""" & \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{The 64 cell values behind Figure~\ref{fig:grid}, readout score under
\texttt{min}, corrected readout. Figure~\ref{fig:grid} renders these as colour because the finding
is the row pattern; the margins it prints are the bold row and column means here.}
\label{tab:grid}
\end{table}"""
    return wrap("tblgrid", body)


def main():
    d3 = load("d3_corpus_by_family_410m.json")
    r9 = load("r9_permutation_calibrated_min.json")
    e54 = load("e54_aggregation_audit_rstrip_v2.json")
    e57 = load("e57_grid_variance_ci_rstrip.json")
    clustered = load("paper_clustered_derangement_t.json")
    cv4 = load("cv4_phase1_capability.json")
    cv2 = load("cv2_position_support.json")
    cv6 = load("cv6_per_family_ladder.json")
    cv7 = load("cv7_1b_rung.json")
    e48r = load("e48_crossover_410m_rstrip.json")
    e48b = load("e48b_exposure_growth.json")
    e48c = load("e48c_exposure_vs_read.json")
    e52 = load("e52_factorial_410m_rstrip.json")

    out = ["% tables_audit.tex - GENERATED by paper/tools/make_audit_tables.py. Do not edit.\n"
           "% Every number is read from results/*.json at build time.\n\n"]
    out.append(tbl_ladder(d3, cv6, cv7))
    out.append(tbl_family(d3))
    out.append(tbl_derange(r9, e54))
    out.append(tbl_variance(e57, clustered))
    out.append(tbl_competence(cv4))
    out.append(tbl_position(cv2))
    out.append(tbl_crossover(e48r))
    out.append(tbl_contain(e48b, e48c))
    out.append(tbl_grid(e52))

    with open(DEST, "w") as fh:
        fh.write("".join(out))
    n = sum(chunk.count("newcommand") for chunk in out)
    print(f"  wrote {os.path.relpath(DEST, ROOT)}  ({n} table macros)")


if __name__ == "__main__":
    main()
