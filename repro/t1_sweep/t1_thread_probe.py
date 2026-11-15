#!/usr/bin/env python3
"""
t1_thread_probe.py — why does a module record torch_num_threads=8 when the default is 10?

THE OBSERVATION. Every compute module in the 2026-08-29 T1 sweep stamped
`torch_num_threads: 8` into its provenance. `cv2_position`, which runs a tokenizer and no parallel
op, stamped 10. A fresh interpreter on this machine reports 10 under every condition tried by hand
(plain, nohup, after a BLAS matmul, after an at::parallel_for elementwise op, and via
`provenance.env_state()` directly).

WHY IT MATTERS. `results/e60_fitter_determinism.json` measured the fitters agreeing EXACTLY at 1, 4
and 8 threads (`cross_implementation_abs = 0.0`) and diverging by ~1.09e-04 at 10 and 12. So which
regime the sweep actually ran in is load-bearing for interpreting bit-identity, and SPEC §1.1c
forbids changing the count. An unexplained 8 is therefore worth pinning down rather than assuming.

METHOD. Each hypothesis runs in its OWN fresh subprocess, because thread state is process-global
and a single interpreter testing them in sequence cannot attribute a change to one cause. Each
child prints the count before and after the candidate action.

  .venv/bin/python repro/t1_sweep/t1_thread_probe.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PRE = (
    "import sys, os; sys.path.insert(0, 'src'); sys.path.insert(0, 'jacobian-lens')\n"
    "import torch\n"
    "before = torch.get_num_threads()\n"
)
POST = "\nprint(f'{before} -> {torch.get_num_threads()}')\n"

# An operator this sweep actually reads.
LENS = "results/e48/lens_INSTREAM_Pile-CC_410m_n200_s0.pt"

CASES = {
    "baseline (import torch only)": "",
    "import transformers": "import transformers",
    "AutoTokenizer.from_pretrained": (
        "from transformers import AutoTokenizer\n"
        "AutoTokenizer.from_pretrained('EleutherAI/pythia-410m-deduped')"
    ),
    "AutoModelForCausalLM.from_pretrained": (
        "from transformers import AutoModelForCausalLM\n"
        "AutoModelForCausalLM.from_pretrained('EleutherAI/pythia-410m-deduped',"
        " dtype=torch.float32)"
    ),
    "import provenance": "from provenance import write_result",
    "import anchor_evals": "from anchor_evals import load_eval",
    "import jlens.hooks + jlens.hf": "from jlens.hooks import ActivationRecorder\nfrom jlens.hf import from_hf",
    f"torch.load({os.path.basename(LENS)})": f"blob = torch.load({LENS!r}, map_location='cpu')",
    "torch.load + .float() the J dict": (
        f"blob = torch.load({LENS!r}, map_location='cpu')\n"
        "J = {int(k): v.float() for k, v in blob['J'].items()}"
    ),
    "BLAS matmul": "a = torch.randn(1500, 1500); b = torch.randn(1500, 1500); c = a @ b",
    "at::parallel_for elementwise": "x = torch.randn(20_000_000); y = x.mul(1.5).sum()",
}


def main():
    os.chdir(ROOT)
    if not os.path.isfile(LENS):
        print(f"  NOTE: {LENS} not present; torch.load cases will error")
    width = max(len(k) for k in CASES)
    print(f"  {'candidate action':<{width}}  before -> after")
    print("  " + "-" * (width + 20))
    hits = []
    for name, body in CASES.items():
        code = PRE + body + POST
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           env={**os.environ})
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else \
            f"ERROR: {r.stderr.strip().splitlines()[-1][:60] if r.stderr.strip() else '?'}"
        flag = ""
        if "->" in out:
            a, b = [x.strip() for x in out.split("->")]
            if a != b:
                flag = "   <== CHANGES THE COUNT"
                hits.append((name, out))
        print(f"  {name:<{width}}  {out}{flag}")
    print()
    if hits:
        for n, o in hits:
            print(f"  CULPRIT: {n}  ({o})")
    else:
        print("  No single action reproduced the drop to 8. The cause is not any one of these,\n"
              "  and remains an open question -- do not guess at it in the write-up.")
    return 0


# ---------------------------------------------------------------- soak mode
# The single-action probe above found nothing. The surviving pattern is TIME: the only module
# that stamped 10 is the only one that finished in ~6s. So sample the count DURING a sustained
# torch workload rather than before and after a single call.
#
#   .venv/bin/python repro/t1_sweep/t1_thread_probe.py --soak
def soak(seconds=150):
    import time
    import torch
    t0 = time.time()
    seen, last = [], None
    a = torch.randn(1400, 1400)
    while time.time() - t0 < seconds:
        a = (a @ torch.randn(1400, 1400)).tanh()
        n = torch.get_num_threads()
        if n != last:
            seen.append((round(time.time() - t0, 1), n))
            print(f"    t={time.time()-t0:7.1f}s  torch_num_threads = {n}", flush=True)
            last = n
    print(f"  transitions: {seen}")
    return seen


if "--soak" in sys.argv:
    print("  soaking with sustained matmul work, printing every change:")
    soak()
    raise SystemExit(0)


if __name__ == "__main__":
    raise SystemExit(main())
