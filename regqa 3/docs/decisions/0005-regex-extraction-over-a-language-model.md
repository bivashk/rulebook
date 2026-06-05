# 5. Regex extraction over a language model

Status: accepted
Date: 2026-08-29

## Context

Phase 3 builds a supersession graph. Its edges come from statements inside
documents such as "in supersession of office order NITR/ES/2014/M/2402". A
wrong edge makes the system answer confidently from a withdrawn notice, which is
the failure this project exists to prevent.

## Decision

Extract document numbers, dates, effective dates and supersession cues with
regular expressions only. No language model in this phase.

## Alternatives considered

- **A language model per document.** Higher recall on unusual phrasings.
  Rejected on three grounds: it costs money against a 500 rupee ceiling; it is
  not deterministic, so a regression cannot fail CI; and it returns an answer for
  every document including those where nothing is stated, which makes low
  coverage indistinguishable from invention.
- **Regex with model fallback on misses.** Retains most of the objection above:
  the fallback fires exactly where the text is unclear, which is where a
  fabricated reference is most likely and least detectable.

## Consequences

- Coverage will be lower than a model would report, and that number is honest.
  Phase 3 gets a graph in which every edge quotes text that exists.
- Cue phrases are a list in one module, extended as the corpus reveals more.
- A cue with no identifiable target is still recorded, with its surrounding text,
  so phase 3 can offer it for human confirmation rather than discarding it.
