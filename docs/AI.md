# AI

Two entirely different things are called "AI" in this project's history,
and conflating them would misrepresent the codebase. They're kept
explicit here.

## Runtime AI (part of the application)

**Provider: local Ollama only.** There is no OpenAI, Anthropic, or any
other hosted LLM API integration anywhere in this codebase - confirmed by
reading `requirements.txt` (only `ollama>=0.4,<1.0`, no `openai`/
`anthropic` package) and by grepping the source for any such usage. The
`Configuration` env vars (`OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`,
`OLLAMA_MAX_TOKENS`) exist because Ollama runs locally, not because
multiple providers are supported - if a hosted provider is ever added,
it should be introduced as a genuinely separate, documented option, not
silently assumed.

**Used for**: resume generation (`app/ai/resume_builder.py` +
`app/ai/resume_generator.py`), cover-letter generation
(`app/ai/cover_letter_builder.py` + `app/ai/cover_letter_generator.py`),
and structured-data extraction from an uploaded CV
(`app/ai/profile_extractor.py`), reachable from the dashboard via
`/generate/<id>`, `/coverletter/<id>`, and `/settings/upload-cv`
respectively. `ProfileExtractor.extract()` was hardened alongside being
wired up to a live route for the first time: it now tolerates the model
wrapping its JSON response in a Markdown code fence (the same class of
bug found in `profiles/profile.json` and `templates/resume_template.html`
elsewhere in this codebase) by extracting the first `{...}` block rather
than assuming a bare JSON response, and raises a clear error instead of
an unhandled `TypeError` if the model doesn't respond at all.

**Not used for**: matching, ranking, deduplication, filtering, or search.
All of that is deterministic Python (`app/search/v2/matching`,
`app/search/v2/ranking`, `app/ai/matcher.py`) - see
`docs/MATCHING_AND_RANKING.md`. This is a deliberate design boundary, not
an oversight: matching/ranking need to be explainable and reproducible
("why did this job rank #3"), which an LLM call would make
non-deterministic and opaque.

### Hallucination prevention

Both generation prompts are explicit and specific:

> "Do not invent experience, skills, education or certifications. Use
> only information contained in the candidate profile."

This is a prompt-level instruction, not a technical guarantee - nothing in
this codebase parses the model's output and cross-checks every claim
against `profiles/profile.json`. It relies on the model following
instructions, which is a real limitation worth knowing about if this is
ever used for something higher-stakes than a personal job search.

### Availability and failure behavior

**Found and fixed this session**: the code path behind the dashboard's
generation buttons (at the time, a separate class - `AIEngine.ask()`,
since removed, see "One Ollama wrapper class" below) called
`ollama.chat()` with no timeout at all, and could hang a Flask request
indefinitely if the local model was slow to respond - reproduced live in
this development environment. It was first hardened with the same
bounded daemon-thread watchdog pattern `LocalLLM` already used, then
that duplicate class was removed entirely once every call site was
migrated onto `LocalLLM` directly (default 30s, configurable via
`OLLAMA_TIMEOUT`), returning `None` on timeout or failure instead of
hanging. The `/generate/<id>` and `/coverletter/<id>` routes catch that
and return a `503` with a plain-language message instead of an unhandled
crash.

**One Ollama wrapper class, not two.** `app/ai/llm.py`'s `LocalLLM` is now
the single local-model client for the whole codebase - used directly by
`app/ai/analyzer.py`, `app/documents/cover_letter_generator.py`, and (as
of this consolidation) `ResumeBuilder`/`CoverLetterBuilder`/
`ProfileExtractor`, which previously went through a separate,
independently-hardened duplicate (`app/ai/ai_engine.py`'s `AIEngine`,
now removed). `LocalLLM.ask()` gained an optional `system` parameter
(sent as a leading system-role message) to support those three call
sites' system+user prompt pattern, while staying fully backward
compatible with existing single-prompt callers. Consolidating onto
`LocalLLM` also fixed a small behavior gap: `AIEngine` defaulted to a
hardcoded `model="llama3.1"` with no auto-detection, while `LocalLLM`
auto-detects whichever model is actually installed when `OLLAMA_MODEL`
isn't set - verified live (`"Local LLM: llama3.1:latest"` reported
correctly after the switch).

**The application works without Ollama.** Matching, ranking, search, the
dashboard, saved jobs, and application tracking all function with zero
dependency on Ollama being installed or running. Only the two generation
buttons require it, and they now fail with a clear message instead of
hanging or crashing when it's unavailable.

## Development AI (used to build this project)

**Claude Code / Claude (Sonnet 5)** was used as a development assistant
for this session: repository analysis, bug investigation (including live
network probing to determine actual root causes rather than trusting
prior documentation), implementation, test-writing, and this
documentation set.

| | Development AI (Claude Code) | Runtime AI (Ollama) |
| --- | --- | --- |
| Role | Coding assistant | Application feature |
| Used for | Analysis, implementation, docs | Resume/cover-letter generation |
| Part of the running application | No | Yes |
| Required to use CareerPilot AI | No | Only for two specific actions |

Nothing in this project's runtime code calls Claude, Anthropic's API, or
any other AI development tool - that distinction matters and is kept
explicit rather than blurred.

## Privacy

Resume/cover-letter prompts include the full candidate profile
(`profiles/profile.json`) and the selected job's description, sent to
whatever `OLLAMA_HOST` points at. With the default `127.0.0.1` host, this
never leaves the local machine. If `OLLAMA_HOST` is ever pointed at a
remote Ollama instance, that changes - worth knowing before doing so.
