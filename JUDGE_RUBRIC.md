# Prompt Bench — Judge Rubric

## Purpose

Prompt Bench evaluates multiple anonymous AI responses to the same prompt.

The Judge does not know which provider created each response. Responses are labeled Answer A, Answer B, and Answer C during evaluation.

Provider identities are preserved separately and reconnected after judging for analytics and Power BI reporting.

The goal is not to select one overall winning model. Prompt Bench identifies the strongest parts of each response and uses them to create one final synthesized answer.

---

# Scored Metrics

Prompt Bench scores five quality metrics from 1 to 5.

## 1. Factual Accuracy

Measures whether factual claims are correct and supported.

### Score Definitions

**5 — Excellent**
- Important factual claims are verified and correct.
- No meaningful factual errors are present.

**4 — Good**
- Correct overall.
- May contain a very small factual imprecision that does not change the answer.

**3 — Mixed**
- Mostly correct.
- Some claims are uncertain, weakly supported, or not fully verified.

**2 — Poor**
- Contains important factual problems.
- Evidence may conflict with major claims.

**1 — Failed**
- Major factual errors are present.
- Claims may be fabricated.
- The core answer may be wrong.

### Factual Reuse Rule

Low factual accuracy blocks unreliable factual claims from being reused during synthesis.

A response may still contribute non-factual qualities such as tone, clarity, or structure.

---

## 2. Completeness

Measures whether the response fully answers the user's request.

### Score Definitions

**5 — Excellent**
- Fully answers the request.
- Adds useful and relevant extra context that improves the answer.

**4 — Complete**
- Fully answers exactly what was asked.
- Nothing important is missing.

**3 — Mostly Complete**
- Answers the main request.
- Some useful or expected information is missing.

**2 — Incomplete**
- Major parts of the request are missing.

**1 — Failed**
- Barely answers the request or misses the core task.

### Completeness Rule

A score of 5 requires Relevance to be at least 4.

More information does not count as higher completeness if the additional information is irrelevant.

---

## 3. Relevance

Measures whether every part of the response helps satisfy the user's request.

### Score Definitions

**5 — Excellent**
- Everything directly supports the user's request.
- Extra context is useful and purposeful.

**4 — Good**
- Highly focused.
- Contains only minor unnecessary detail.

**3 — Mixed**
- The main answer is relevant.
- Noticeable filler, repetition, or tangents are present.

**2 — Poor**
- A significant portion of the response does not help answer the request.

**1 — Failed**
- Mostly off-topic.
- Misunderstands or ignores the user's intent.

---

## 4. Tone

Measures whether the voice and style fit the user, situation, and any explicit style request.

### Score Definitions

**5 — Excellent**
- The tone fits the user and situation extremely well.
- Feels natural and appropriate.

**4 — Good**
- Appropriate overall.
- May be slightly stiff, generic, or mismatched.

**3 — Acceptable**
- Not inappropriate, but noticeably imperfect for the context.

**2 — Poor**
- The tone interferes with the response or clearly misreads the situation.

**1 — Failed**
- Strongly inappropriate, patronizing, insensitive, or completely wrong for the context.

### Tone Rule

If the user explicitly requests a tone or style and the response ignores that instruction, the Tone score is capped.

---

## 5. Clarity

Measures how easily the user can understand the answer.

### Score Definitions

**5 — Excellent**
- Immediately understandable.
- Main point is obvious.
- Structure and wording fit the user's level.

**4 — Good**
- Easy to follow.
- Contains only minor awkwardness or unnecessary complexity.

**3 — Understandable**
- Meaning is present, but the user has to work somewhat to follow it.

**2 — Poor**
- Confusing because of jargon, poor organization, contradictions, or unclear wording.

**1 — Failed**
- Very difficult to understand.
- The main point is lost.

---

# Instruction Following

Instruction Following is a rule layer, not a scored metric.

## PASS

The response followed all important explicit instructions.

Examples:
- correct format
- correct number of bullets
- requested word limit
- requested tone
- requested structure

## PARTIAL

The response completed the main task but missed a smaller instruction.

## FAIL

The response ignored or broke an important instruction.

### Rule

Instruction Following only affects the relevant part of the response.

For example:

- A formatting failure does not make factual information inaccurate.
- Ignoring a requested tone may limit the Tone score.
- Missing a required format must be corrected during synthesis.

---

# Cross-Metric Rules

Prompt Bench intentionally uses a small number of cross-metric relationships.

Metrics are scored independently first.

Cross-metric rules are applied afterward to catch logical contradictions.

## Completeness and Relevance

A Completeness score of 5 requires Relevance to be at least 4.

## Tone and Instruction Following

If the user explicitly requested a style or tone and the response ignored it, the Tone score is capped.

## Factual Accuracy and Synthesis

Low factual accuracy blocks unreliable factual claims from being reused.

This does not automatically block Tone, Clarity, organization, or other non-factual strengths from being reused.

---

# Factual Verification

Prompt Bench should verify important factual claims when verification is necessary.

## Standard Verification

Use at least:

- 2 strong independent sources

## Expanded Verification

Use 3 or more sources when:

- sources disagree
- the claim is controversial
- the claim is high-stakes
- the claim is time-sensitive
- the first two sources conflict

## Source Priority

Prefer:

1. Primary or official sources
2. Original research or data
3. Strong independent secondary sources

Multiple websites repeating the same original source do not count as independent confirmation.

Time-sensitive claims should use current evidence.

---

# Agent Consensus

Agreement between AI agents is used as a confidence signal.

It is not treated as proof.

## Consensus Levels

**3 of 3 agree**
- High initial consensus

**2 of 3 agree**
- Majority consensus
- The disagreement should be verified

**0 of 3 agree**
- Low consensus
- Stronger factual verification is required

### Important Rule

Two agents agreeing does not automatically make their answer correct.

External evidence can overturn the majority.

---

# Blind Judging

The Judge sees:

- Answer A
- Answer B
- Answer C

The Judge does not see provider names.

Answer labels may be randomized on each run.

The system privately preserves the provider mapping.

Example:

Answer A → Gemini  
Answer B → OpenAI  
Answer C → Claude

After judging is complete, provider identities are restored for analytics and Power BI reporting.

---

# Judge Output

For each anonymous answer, the Judge should return:

- Factual Accuracy score
- Factual Accuracy reason
- Completeness score
- Completeness reason
- Relevance score
- Relevance reason
- Tone score
- Tone reason
- Clarity score
- Clarity reason
- Instruction Following result
- Best Use
- Do Not Use

Example:

Answer A

Factual Accuracy: 5  
Reason: Core factual claims were verified.

Completeness: 4  
Reason: Fully answered the question but did not add useful extra context.

Relevance: 5  
Reason: Every part directly supported the request.

Tone: 3  
Reason: Appropriate but somewhat stiff.

Clarity: 4  
Reason: Easy to understand.

Instruction Following: PASS

Best Use:
- verified factual content
- concise structure

Do Not Use:
- none

---

# Category Leaders

Prompt Bench does not choose one overall winner.

Instead, the Judge identifies the strongest answer for each category.

Example:

Best Factual Accuracy → Answer B  
Best Completeness → Answer C  
Best Relevance → Answer A  
Best Tone → Answer C  
Best Clarity → Answer A

The synthesis agent uses these category strengths to build one final answer.

---

# Tie Rules

A tie means multiple responses remain eligible.

Prompt Bench still selects one primary contributor when possible.

## Completeness Tie

Higher Relevance wins.

## Relevance Tie

Higher Clarity wins.

## Tone Tie

If an explicit tone or style was requested:

Better Instruction Following wins.

Otherwise:

Higher Clarity wins.

## Clarity Tie

Higher Relevance wins.

If the tiebreaker is also tied, Prompt Bench may select either response instead of inventing false precision.

Factual disagreements are handled separately through Agent Consensus and external verification.

---

# Synthesis Rules

The synthesis agent receives:

- original user prompt
- anonymous responses
- Judge scores
- score explanations
- Best Use guidance
- Do Not Use guidance
- category leaders
- verified factual information

The synthesis agent should:

- use verified factual content
- use the strongest relevant details
- use the strongest appropriate tone
- use the clearest structure
- avoid blocked factual claims
- avoid irrelevant content
- avoid duplicate information
- follow explicit user instructions

A tied response is an eligible contributor, not a mandatory contributor.

---

# Final QA Gate

Before the final answer is shown to the user, Prompt Bench performs one final QA check.

The final check evaluates:

## Facts
Did rejected or disputed information reappear?

## Instructions
Were explicit user requirements followed?

## Relevance
Did synthesis add unnecessary information?

## Duplication
Did combining responses create repeated ideas?

## Clarity
Does the final response read like one coherent answer?

### Final QA Results

**PASS**
- Show the answer to the user.

**REVISE**
- Send specific correction instructions to the synthesis agent.
- Rewrite once.
- Run the final QA check again.

Version 1 allows one automatic revision.

---

# Analytics-Only Overall Score

Prompt Bench calculates a weighted Overall Score for analytics and Power BI.

This score does not choose an overall winner and does not control synthesis.

## Weights

Factual Accuracy: 30%  
Completeness: 20%  
Relevance: 20%  
Tone: 15%  
Clarity: 15%

## Formula

Overall Score =

(Factual Accuracy × 0.30)  
+ (Completeness × 0.20)  
+ (Relevance × 0.20)  
+ (Tone × 0.15)  
+ (Clarity × 0.15)

The Overall Score is used only for reporting, analytics, and provider performance comparisons.

---

# Version

Prompt Bench Judge Rubric — Version 1