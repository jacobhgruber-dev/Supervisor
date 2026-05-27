# Verify Quotes Mode

**Trigger:** `verifyquotes`, `/verifyquotes`, `auditquotes`, or `/auditquotes`

Painstaking quotation audit mode. Goes line-by-line. Verifies each quotation matches its claimed source. Detects unwanted paraphrasing. Flags every uncertainty. Outputs a clear summary table or list of issues before suggesting fixes.

## Why This Behavior

Large language models have a well-documented tendency to hallucinate — and one specific form of hallucination is "quote drift": the model recalls the gist of a quotation but subtly changes the wording, presenting a paraphrase as an exact quote. In casual conversation this is harmless. In journalism, academia, legal documents, or publishing, it's a serious error that damages credibility. Verify Quotes mode counters this by forcing the AI to treat every quoted passage as suspect until confirmed. It adds friction deliberately — the kind of friction a human fact-checker applies — to catch errors the AI would otherwise breeze past.

## When to Use

- Reviewing articles, papers, or reports that quote sources
- Fact-checking before publication
- Legal or compliance documents where exact wording matters
- Academic work with citations
- Journalism and editorial review
- Detecting AI-generated content that paraphrases instead of quoting

## What It Changes

- Compares every quoted passage to its cited source
- Flags any difference between the quote and the original text
- Detects paraphrasing disguised as direct quotation
- Marks confidence level for each finding (verified / minor variance / unverified)
- Outputs structured results: table or bullet list of issues
- Never "improves" quotes — only reports accuracy

## Example

> verifyquotes Check all quotations in this draft article against their linked sources.
