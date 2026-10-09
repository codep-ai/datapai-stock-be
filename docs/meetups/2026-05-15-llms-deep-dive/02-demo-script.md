# Demo Script — LLM Router (15 min)

Goal: show, live, that routing per-request beats one-model-for-everything on cost without losing quality. Self-contained Python — no dependency on the stock-be repo so it runs on a fresh machine.

## Setup (before the call)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install google-generativeai openai anthropic   # qwen via local ollama optional
export GEMINI_API_KEY=...   OPENAI_API_KEY=...   ANTHROPIC_API_KEY=...
```

Have `router_demo.py` (below) ready. Pre-run once so model weights/keys are warm.

## Beat 1 — the problem (2 min)

Show the 4 prompts on screen. Ask chat: "which model would you use for each?"
1. `"Is this message spam? 'WIN a free iPhone click here'"` — trivial
2. `"Summarize this 8k-token earnings call into 5 bullets"` — long context
3. `"Call get_stock_price for AAPL then explain the move"` — tool-calling
4. `"Write a careful risk disclosure for a leveraged CFD product"` — careful reasoning

## Beat 2 — naive: everything to GPT-4o (3 min)

Run `router_demo.py --route all-gpt4o`. Show: it works, but print the running $ total. ~$X for 4 calls. Extrapolate on slide: ×100k/mo.

## Beat 3 — the router (5 min)

Run `router_demo.py --route smart`. Walk the routing table live:
- prompt 1 → Gemini Flash (classify, cheap)
- prompt 2 → Gemini Flash (big context, cheap) — note the win
- prompt 3 → gemini-2.5-flash (NOT lite — say why out loud)
- prompt 4 → Claude Sonnet (careful writing)

Show same-or-better answers at ~1/10th the cost. This is the money slide.

## Beat 4 — the cascade (3 min)

Run `router_demo.py --route smart --force-fail prompt3`. Cheap model returns empty/garbage → router detects → escalates to GPT-4o → succeeds. Point out: this is why you fail-open and check the response, not just trust it.

## Beat 5 — cost projection (2 min)

Run `router_demo.py --project 100000`. Prints the table:
```
all-gpt4o:        $1,520 / mo
smart route:      $   190 / mo
saving:           87%
```
Land the takeaway: "this is one config file and a response check."

---

## router_demo.py (skeleton — fill provider calls)

```python
import argparse, time

PRICES = {  # USD per 1M tokens, blended — VERIFY LIVE
    "gemini-flash": 0.30, "gpt-4o": 6.0, "claude-sonnet": 9.0, "qwen-local": 0.0,
}

def classify(prompt: str) -> str:
    p = prompt.lower()
    if "spam" in p or len(prompt) < 120:        return "gemini-flash"   # trivial
    if len(prompt) > 2000:                       return "gemini-flash"   # long ctx, cheap
    if "call " in p or "tool" in p:              return "gemini-flash"   # 2.5-flash, NOT lite
    if "risk" in p or "disclosure" in p:         return "claude-sonnet"  # careful
    return "gpt-4o"

def call(model, prompt, force_fail=False):
    t = time.time()
    if force_fail:                       # simulate the lite-empty-response gotcha
        return "", 0, time.time() - t
    # TODO: real provider SDK call per `model`; return (text, tokens, latency)
    text, tokens = f"[{model} answer]", 1800
    return text, tokens, time.time() - t

def cost(model, tokens):                 # tokens -> $
    return PRICES[model] * tokens / 1_000_000

def run(prompt, route, force_fail=False):
    model = "gpt-4o" if route == "all-gpt4o" else classify(prompt)
    text, tokens, lat = call(model, prompt, force_fail)
    if not text and route == "smart":            # cascade: escalate on empty
        model = "gpt-4o"
        text, tokens, lat = call(model, prompt)
    return model, tokens, lat, cost(model, tokens)

PROMPTS = [
    "Is this spam? 'WIN a free iPhone click here'",
    "Summarize this earnings call into 5 bullets: " + "blah " * 1000,
    "Call get_stock_price for AAPL then explain the move",
    "Write a careful risk disclosure for a leveraged CFD product",
]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", default="smart")
    ap.add_argument("--force-fail", default="")
    ap.add_argument("--project", type=int, default=0)
    a = ap.parse_args()
    total = 0.0
    for i, p in enumerate(PROMPTS):
        ff = a.force_fail == f"prompt{i+1}"
        m, tok, lat, c = run(p, a.route, ff)
        total += c
        print(f"#{i+1:>1}  {m:<14} {tok:>5}tok {lat*1000:5.0f}ms  ${c:.5f}")
    print(f"TOTAL 4 calls: ${total:.5f}")
    if a.project:
        per_req = total / 4
        print(f"PROJECTED {a.project:,}/mo: ${per_req*a.project:,.0f}")
```

Note: keep the live API calls behind a `--live` flag; default to stubbed answers so the demo never blocks on a rate limit in front of 80 people. Show one real `--live` call at the end if time allows.
