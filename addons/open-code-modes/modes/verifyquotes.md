# Verify Quotes Mode

**Trigger:** `verifyquotes`, `/verifyquotes`, `auditquotes`, or `/auditquotes`

Painstaking quotation audit mode. Goes line-by-line, character-by-character. Verifies each quotation matches its claimed source. Detects unwanted paraphrasing. Flags every uncertainty. Outputs a clear summary table or list of issues before suggesting fixes.

## Why This Behavior

Large language models have a well-documented tendency to hallucinate — and one specific form of hallucination is "quote drift": the model recalls the gist of a quotation but subtly changes the wording, presenting a paraphrase as an exact quote. In casual conversation this is harmless. In journalism, academia, legal documents, or publishing, it's a serious error that damages credibility. Verify Quotes mode counters this by treating every quoted passage as suspect until confirmed — the kind of friction a human fact-checker applies.

## What It Covers

Non-negotiable rules:
1. **NEVER alter, paraphrase, or "improve" any quotation.** Copy the exact original text only.
2. **Every quote, name, date, and factual claim must be grounded** strictly in the provided source text or files.
3. **If a source is missing, unclear, or ambiguous**, respond with: "Unverified — please provide the exact source text."
4. **Detect and flag any accidental paraphrasing** that appears inside quotation marks.
5. **Flag every uncertainty** — "Possible drift detected here — human review recommended."
6. **Go line by line** — every quoted passage gets individually verified against its source.

Process: extract every quotation, locate each in the source, compare character by character (exact words, punctuation, capitalization, whitespace), and flag any deviation no matter how small.

## What It Changes

- Compares every quoted passage to its cited source
- Flags any difference between the quote and the original text — no matter how small
- Detects paraphrasing disguised as direct quotation
- Marks confidence level for each finding (verified / minor variance / unverified)
- Outputs structured results: table or bullet list of issues
- Never "improves" quotes — only reports accuracy
- When in doubt, marks for human review rather than guessing

## When to Use

- Reviewing articles, papers, or reports that quote sources
- Fact-checking before publication
- Legal or compliance documents where exact wording matters
- Academic work with citations
- Journalism and editorial review
- Detecting AI-generated content that paraphrases instead of quoting
- Verifying transcript quotes, biblical/historical sources

## Example

> verifyquotes Check all quotations in this draft article against their linked sources.
