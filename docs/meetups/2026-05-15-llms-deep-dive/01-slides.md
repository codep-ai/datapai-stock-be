# Session 6 — LLMs Deep Dive: When To Use Which Model

**Data & AI Group — Learning & Practice** · 15 May 2026, 8:00 PM (online)
Host: Donny Z. · ~80 attendees, most new · 50 min

---

## Slide 1 — Welcome (1 min)

- 80+ of you, many first-timers — welcome.
- House rules: mics muted, questions in chat, demo + hands-on, no slides to read later you can't have — repo link dropped at the end.
- Tonight is **practical**: not "how transformers work", but **"which model do I actually call, and how do I not go broke doing it."**

---

## Slide 2 — The only question that matters in production (3 min)

> You don't pick a model. You pick a model **per request**.

The same app sends:
- a one-line classification ("is this spam?") → tiny/cheap model
- a 30-page contract summary → big-context model
- a tool-calling agent step → a model that does function-calling reliably

Using GPT-4-class for all three burns money. Using a tiny model for all three burns trust.

**Takeaway: routing is the product, not the model.**

---

## Slide 3 — The 2026 menu (5 min)

| Family | Sweet spot | Watch out for |
|---|---|---|
| **Gemini Flash** (2.5-flash) | cheap, fast, big context, solid function-calling | `*-lite` silently returns empty after a function-call round — avoid for tool use |
| **GPT-4o / o-series** | strong reasoning, mature tool ecosystem | priciest per token; rate limits under burst |
| **Claude Sonnet/Opus** | long-context reasoning, careful writing, code | cost; refusals if prompt looks unsafe |
| **Llama 3.x (open)** | self-host, data stays in your VPC, no per-token cost | you own the GPU bill + ops |
| **Qwen 2.5 (open)** | strong multilingual, runs local/cheap | smaller ecosystem, eval before trusting |

Rule of thumb:
- **Volume + simple → cheap hosted (Gemini Flash) or local (Qwen).**
- **Hard reasoning, low volume → Claude/GPT.**
- **Data can't leave the building → Llama/Qwen self-hosted.**

---

## Slide 4 — The cost reality (4 min)

Rough order-of-magnitude (USD / 1M tokens, blended in:out — *verify live, prices move*):

- Gemini Flash: ~$0.10–0.40
- GPT-4o: ~$2.50–10
- Claude Sonnet: ~$3–15
- Llama/Qwen self-hosted: ~$0 marginal, but fixed GPU/hr

**The 20–50× spread is the whole game.** If 90% of your traffic is easy and you route it to Flash, you cut the bill by an order of magnitude with near-zero quality loss.

Live math we'll do in the demo: 100k requests/month, avg 2k tokens.
- All GPT-4o: ~$1,500/mo
- 90% Flash / 10% GPT-4o: ~$200/mo

---

## Slide 5 — How an LLM router works (5 min)

```
request ──▶ classifier ──▶ pick tier ──▶ call model ──▶ check ──▶ ✅ return
              (cheap/rule)     │                          │
                               │                          └─ fail/empty ─┐
                               ▼                                          │
                          escalate tier ◀──────────────────────────────────┘
```

Decision inputs:
1. **Task type** — classify / summarize / tool-call / freeform
2. **Token budget** — does it fit the cheap model's context?
3. **Cost ceiling** — per-tenant / per-feature spend cap
4. **Quality floor** — confidence or eval score; below it → escalate

Three patterns:
- **Static route** — config map: task → model. Simple, predictable.
- **Cascade / fallback** — try cheap, escalate on failure or low confidence.
- **Learned route** — a small classifier predicts the cheapest model that will succeed.

Start with static. Add cascade. Earn the learned router with data.

---

## Slide 6 — Production gotchas (4 min)

Hard-won, from a real fintech chat stack:

- **`gemini-2.5-flash-lite` silently returns empty** after a function-call round. Use `gemini-2.5-flash` for any tool use.
- **Fail-open, not fail-closed.** If your router/governance layer flakes, degrade and answer — don't 500. A blocked customer is worse than a slightly-worse answer.
- **Normalize the response envelope.** Every provider returns tool calls differently. Adapt at the boundary so the rest of your code is provider-agnostic.
- **Strip "thinking" parts** before showing output (Gemini/Claude reasoning traces leak otherwise).
- **Pin model versions.** "Latest" changes under you and breaks evals overnight.
- **Cost cap per tenant**, enforced server-side, not in the prompt.

---

## Slide 7 — Demo (15 min)

Live: an LLM router deciding per request.
- Same 4 prompts, routed to Gemini Flash / GPT-4o / Claude Sonnet / local Qwen
- Watch the chosen tier, latency, token count, $ per call
- Force a failure → watch the cascade escalate
- Run the 100k/mo cost projection live

(see `02-demo-script.md`)

---

## Slide 8 — Hands-on (15 min)

You get 4 prompts and a scorecard. As a group we rate each model on **accuracy / speed / cost** and decide the route.

(see `03-handson-tasks.md` — drop your scores in chat)

---

## Slide 9 — Open discussion (remaining time)

Seed questions:
- Where are you overspending on a too-big model right now?
- Fine-tune vs route vs prompt — when is each actually worth it?
- Who's self-hosting? What's your real $/token vs hosted?
- Where have LLMs burned you in prod?

---

## Slide 10 — Takeaways + next session

1. Pick a model **per request**, not per app.
2. Start static, add a cascade, measure before you "learn" anything.
3. The cheap-model 20–50× cost spread is free money if you route well.
4. Fail-open, pin versions, normalize the envelope.

Repo + slides + exercises: *(drop link in chat)*
Session 7 preview: RAG that doesn't lie — retrieval + grounding.
