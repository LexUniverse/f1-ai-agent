# Feature Research

**Domain:** Formula 1 Q&A assistant (historical + live data)
**Researched:** 2026-03-26
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Natural-language Q&A for drivers, teams, races, standings | Core expectation for any "assistant" product | MEDIUM | Must reliably answer in RU with EN source grounding where needed |
| Season schedules, race results, and standings lookup | Baseline F1 companion behavior in official and community apps | LOW | Serve from RAG first; fallback to live API for latest round |
| Live-session awareness (practice/qualifying/race status) | Users expect in-session context, not static answers | MEDIUM | Include session state in answer headers and freshness timestamp |
| Source-backed answers with uncertainty handling | Fan assistants are penalized hard for wrong confident answers | HIGH | Must show citation/source type and degraded mode when API fails |
| Race alerts and "never miss session" reminders | Official F1 products emphasize notifications as essential utility | MEDIUM | User-configurable non-spoiler mode is expected by many users |
| Driver/team comparison queries | Common fan task ("X vs Y this season / all-time") | MEDIUM | Needs normalized stats model across historical + current season data |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dual-time-horizon answers (historical context + live race implications in one response) | Gives "analyst-level" answers, not just fact retrieval | HIGH | Combine archived stats with live event deltas in one reasoning pass |
| Explainability mode ("show me why") with compact evidence cards | Builds trust and reduces hallucination complaints | HIGH | Include key facts, source names, and confidence score per claim |
| Strategy-aware insights (tyre windows, pit-stop context, DRS/race-control impacts) | Aligns with what advanced fans value in premium timing products | HIGH | Pull from telemetry/race-control style feeds when available |
| Personal F1 memory layer (favorite team/driver, skill level, language style) | Improves retention and relevance without heavy UI complexity | MEDIUM | Start lightweight (preferences + response style), expand later |
| Conversational "race companion" mode during live sessions | Moves product from Q&A tool to real-time co-pilot | HIGH | Requires aggressive latency control and graceful fallback messaging |
| RU-first educational onboarding for new fans | Strong fit for target audience in `PROJECT.md` | MEDIUM | Explain terms ("undercut", "delta", "parc ferme") contextually |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Fully autonomous race predictions with high-confidence winner calls | Fans like predictive content | Encourages overconfident output; weak trust when misses happen | Provide scenario-based probabilities with explicit assumptions |
| "Real-time everything" telemetry ingestion from every possible source | Sounds comprehensive | High infra cost and fragility; unnecessary for MVP validation | Curate key live signals (session status, standings, major incidents) |
| Social feed / mini-Twitter inside assistant | Perceived engagement feature | Adds moderation, abuse, and content rights complexity | Keep focus on trusted Q&A + concise digests |
| Voice-first assistant for v1 | Feels modern | Out of scope in `PROJECT.md`; adds ASR/TTS latency and quality risk | Text-first chat with structured cards and optional later voice |
| Per-user deep personalization engine from day one | "AI should know me" expectation | Premature complexity before accuracy baseline is proven | Start with explicit preferences and simple profile memory |

## Feature Dependencies

```text
[Source-backed Q&A]
    └──requires──> [Historical data index (RAG)]
                       └──requires──> [Data normalization + schema contracts]

[Live-session awareness]
    └──requires──> [Live API connector + freshness checks]
                       └──requires──> [Degraded mode + uncertainty messaging]

[Driver/team comparison]
    └──requires──> [Unified stat model across seasons]

[Strategy-aware insights]
    └──requires──> [Telemetry/race-control event ingestion]
                       └──requires──> [Event interpretation rules]

[Race companion mode] ──enhances──> [Live-session awareness]
[Personal memory layer] ──enhances──> [Natural-language Q&A]

[Voice-first assistant] ──conflicts──> [v1 latency/accuracy focus]
[Social feed] ──conflicts──> [Core reliability roadmap]
```

### Dependency Notes

- **Source-backed Q&A requires historical index and schema contracts:** retrieval quality and field consistency determine answer correctness.
- **Live-session awareness requires degraded mode:** without explicit fallback behavior, API outages become hallucinations.
- **Strategy insights require event interpretation rules:** raw telemetry without domain interpretation creates noisy or misleading output.
- **Race companion mode depends on live-awareness baseline:** real-time conversational mode is not stable unless core live data flow is already robust.
- **Voice-first conflicts with v1 goals:** adds latency and complexity against the stated 10-second response and 98% accuracy priorities.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Reliable RU-first F1 Q&A with source-backed responses and explicit uncertainty.
- [ ] Historical RAG coverage for seasons, races, drivers, teams, and standings (1950-present where data permits).
- [ ] Conditional live API augmentation for current-session status/results when RAG is stale.
- [ ] Degraded mode messaging when live API/data freshness checks fail.
- [ ] Core utility notifications (session start reminders, optional non-spoiler mode).

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Explainability mode with evidence cards and per-claim confidence — add when core answer accuracy is stable.
- [ ] Enhanced live race companion interactions (incident summaries, momentum shifts) — add when live latency SLO is consistently met.
- [ ] Strategy-focused insights (tyre stint narratives, pit-window comparisons) — add when telemetry ingestion is proven reliable.

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Voice interaction (ASR/TTS) — defer until text UX and response quality are mature.
- [ ] Advanced personalization/recommendation engine — defer until enough behavior data exists.
- [ ] Multi-sport expansion — defer to protect F1 depth and trust moat.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Source-backed RU-first F1 Q&A | HIGH | MEDIUM | P1 |
| Historical RAG + stat normalization | HIGH | HIGH | P1 |
| Live API conditional augmentation + degraded mode | HIGH | MEDIUM | P1 |
| Session reminders + non-spoiler notification mode | MEDIUM | MEDIUM | P1 |
| Explainability evidence cards | HIGH | HIGH | P2 |
| Strategy-aware live insight layer | MEDIUM | HIGH | P2 |
| Personal memory/preferences layer | MEDIUM | MEDIUM | P2 |
| Voice interface | LOW | HIGH | P3 |
| Social/community feed | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Live timing/telemetry | Official F1 App offers premium live telemetry, tracker, tyre/DRS context | Apple TV 2026 F1 coverage adds multiview + telemetry/timing feeds | Keep telemetry selective; convert into plain-language answers |
| Schedules/results/standings | Official F1 App emphasizes race hub + current/past results | Community apps built on f1db/jolpica provide broad historical coverage | Blend deep history + current season in one conversational interface |
| Notifications/non-spoiler | Official F1 App supports session alerts and non-spoiler settings | Sports ecosystems emphasize personalized timely notifications | Provide user-controlled reminders tied to chat context |
| Personalization | Official 2025 app relaunch highlights multi-driver/team tracking | General sports apps personalize feeds by user preference | Lightweight memory + preference-aware responses before heavy recommender systems |

## Sources

- Formula 1 official app feature overview (2022): https://www.formula1.com/en/latest/article/never-miss-a-moment-with-the-official-f1-app.4VryQGIJyCKZJp2eSNj4L5  (MEDIUM)
- Formula 1 official app relaunch and personalization update (2025): https://www.formula1.com/en/latest/article/formula-1-launches-new-website-and-personalised-mobile-app.1knZbPSCZ2tS2z6ADRn2Gs  (HIGH)
- Apple TV Formula 1 integration details (2026): https://www.formula1.com/en/latest/article/apple-reveal-details-of-f1-integration-on-apple-tv-apple-maps-apple-news-and.4JJY1CUT4eobqZ78wTcO3L  (MEDIUM)
- Official Formula 1 App App Store listing (version/features snapshot): https://apps.apple.com/gb/app/official-f1-app/id835022598  (MEDIUM)
- F1DB dataset scope and update cadence (all-time historical data): https://raw.githubusercontent.com/f1db/f1db/main/README.md  (HIGH)
- Jolpica F1 API endpoint coverage (Ergast-compatible): https://raw.githubusercontent.com/jolpica/jolpica-f1/main/docs/README.md  (HIGH)

---
*Feature research for: Formula 1 assistant*
*Researched: 2026-03-26*
