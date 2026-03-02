---
name: model-fallback
description: Monitor token usage across OpenCode sessions and automatically switch to the next available free model when the current one hits its rate limit. Use this skill when orchestrating OpenCode to ensure continuity without interrupting the workflow. All models in the fallback chain are free via Google Antigravity OAuth or OpenCode Zen free tier.
license: MIT
compatibility: opencode
metadata:
  audience: orchestrator-agents
  workflow: model-management
---

## What I do

- Track cumulative token usage for the active model in the current session
- Detect when a model is approaching its rate limit
- Switch OpenCode to the next free model in the fallback chain automatically
- Resume the interrupted task seamlessly after switching
- Log every switch with reason and timestamp

## Prerequisite — Free models setup

All models in this skill require the **opencode-antigravity-auth** plugin authenticated with a Google account. Add to `opencode.json`:

```json
{
  "plugin": ["opencode-antigravity-auth@latest"]
}
```

Then run `/connect` in the TUI, select Google, and authenticate via OAuth. No API key or credit card required.

## Model fallback chain

Switch in this exact order. All models are **free**. Never skip levels unless a model is confirmed down:

| Priority | Model ID | Name | Context | Switch when |
|----------|----------|------|---------|-------------|
| 1 | `google/antigravity-gemini-3-flash` | Gemini 3 Flash | 1,048,576 tokens | **Default starting model** |
| 2 | `google/antigravity-gemini-3-pro` | Gemini 3 Pro | 1,048,576 tokens | Flash quota exhausted |
| 3 | `google/antigravity-claude-sonnet-4-5` | Claude Sonnet 4.5 | 200,000 tokens | Gemini 3 Pro quota exhausted |
| 4 | `google/antigravity-claude-opus-4-5` | Claude Opus 4.5 | 200,000 tokens | All Gemini models exhausted |

**Secondary fallback** (Zen free tier, no Antigravity needed):

| Priority | Model ID | Notes |
|----------|----------|-------|
| 5 | `zen/kimi-k2-5-free` | Kimi K2.5 — free, data may be used for training |
| 6 | `zen/glm-5-free` | GLM-5 — free, data may be used for training |

If all models are exhausted, pause and notify the user.

## Token tracking

Maintain a running counter per model:

```
session_tokens = {
  "google/antigravity-gemini-3-flash": 0,
  "google/antigravity-gemini-3-pro": 0,
  "google/antigravity-claude-sonnet-4-5": 0,
  "google/antigravity-claude-opus-4-5": 0,
  "zen/kimi-k2-5-free": 0,
  "zen/glm-5-free": 0
}
```

After every OpenCode interaction, add input tokens + output tokens to the active model's counter.

### Switch thresholds (act before hitting the hard limit)

| Model | Switch at | Hard limit |
|-------|-----------|------------|
| `antigravity-gemini-3-flash` | 900,000 tokens | ~1,048,576 |
| `antigravity-gemini-3-pro` | 900,000 tokens | ~1,048,576 |
| `antigravity-claude-sonnet-4-5` | 170,000 tokens | ~200,000 |
| `antigravity-claude-opus-4-5` | 170,000 tokens | ~200,000 |
| `zen/kimi-k2-5-free` | 900,000 tokens | ~1,000,000 |
| `zen/glm-5-free` | 900,000 tokens | ~1,000,000 |

Also switch immediately if OpenCode returns a rate limit error regardless of the counter.

## How to switch models

### Step 1 — Finish the current atomic unit of work
Never switch mid-file-write or mid-function. Complete the smallest meaningful unit first.

### Step 2 — Switch model via TUI command

```bash
# In the TUI, type:
/models
# Then select the next model from the list

# Or via CLI flag for the next session:
opencode --model google/antigravity-gemini-3-pro
```

Or update `opencode.json` programmatically:

```json
{
  "model": "google/antigravity-gemini-3-pro"
}
```

### Step 3 — Log the switch

```
[2026-02-19 14:32:01] SWITCH: antigravity-gemini-3-flash → antigravity-gemini-3-pro
  Reason: token threshold reached (901,234 / 900,000)
  Task: "Refactoring auth module"
  All token counters: flash=901,234 | pro=0 | sonnet=0 | opus=0
```

### Step 4 — Resume the task

After switching, orient the new model with one line:

> "Continuing: [task]. Previous model (gemini-3-flash) hit rate limit. Resuming from: [last checkpoint]."

## Multi-account rotation (advanced)

If you have multiple Google accounts configured in Antigravity, the plugin rotates automatically between them when one hits a rate limit. This effectively multiplies your free quota. To add more accounts run `opencode auth login` again.

## When all models are exhausted

1. Stop OpenCode operations immediately
2. Save task state to `session-state.md`:

```markdown
## Session paused — all free models exhausted

**Date**: 2026-02-19 15:00:00  
**Task**: Refactoring auth module — 70% complete  
**Last file**: src/auth/login.ts  
**Resume from**: function `validateToken()` line 142  

| Model | Tokens used |
|-------|-------------|
| antigravity-gemini-3-flash | 901,234 |
| antigravity-gemini-3-pro | 902,000 |
| antigravity-claude-sonnet-4-5 | 171,000 |
| antigravity-claude-opus-4-5 | 172,500 |
| zen/kimi-k2-5-free | 901,000 |
| zen/glm-5-free | 900,500 |

**Action**: Wait for quota reset (usually resets daily) or add more Google accounts.
```

3. Notify the user with what was completed and what remains.

## Rules

- **Never switch during a file write** — complete writes first
- **Never lose context** — summarize task state before switching if the context window resets
- **Always prefer free models** — never suggest paid models as long as free ones are available
- **Be transparent** — always tell the user when a switch happens and why
- **Counters reset each session** — do not carry over counts from previous sessions
