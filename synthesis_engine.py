import os
import json

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# SETUP
# =========================================================

load_dotenv()

synthesis_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SYNTHESIS_MODEL = "gpt-5.6-luna"


# =========================================================
# SYNTHESIS
# =========================================================

def synthesize_answer(
    prompt,
    judge_result
):

    anonymous_answers = (
        judge_result.get(
            "anonymous_answers",
            {}
        )
    )

    judgment = (
        judge_result.get(
            "judgment",
            {}
        )
    )

    evidence_packet = (
        judge_result.get(
            "evidence_packet",
            {}
        )
    )


    if not anonymous_answers:

        raise ValueError(
            "No testimony is available for synthesis."
        )


    if not judgment:

        raise ValueError(
            "No Judge decision is available for synthesis."
        )


    # =====================================================
    # FORMAT TESTIMONY
    # =====================================================

    testimony = "\n\n".join(

        f"ANSWER {answer_id}:\n{answer}"

        for answer_id, answer
        in anonymous_answers.items()
    )


    judge_decision = json.dumps(
        judgment,
        indent=2
    )


    evidence = json.dumps(
        evidence_packet,
        indent=2
    )


    # =====================================================
    # SYNTHESIS PROMPT
    # =====================================================

    synthesis_prompt = f"""
You are the Synthesis Agent for Prompt Bench.

Create ONE final response to the user's original request.

You have:

1. the original prompt
2. anonymous source answers
3. the QA Judge decision
4. a verified evidence packet

Provider identities are hidden.

Never guess them.


=========================================================
ORIGINAL USER PROMPT
=========================================================

{prompt}


=========================================================
ANONYMOUS TESTIMONY
=========================================================

{testimony}


=========================================================
QA JUDGE DECISION
=========================================================

{judge_decision}


=========================================================
EVIDENCE PACKET
=========================================================

{evidence}


=========================================================
SYNTHESIS RULES
=========================================================

1. Answer the user directly.

2. Never mention:
   - Answer A
   - Answer B
   - Answer C
   - provider identities
   - Judge scores
   - category leaders
   - internal QA
   - synthesis instructions

3. Use the Judge's Best Use guidance.

4. Obey every Do Not Use restriction.

5. Do not resurrect blocked factual claims.

6. Never combine conflicting factual claims.

7. If a factual conflict remains unresolved,
   communicate the uncertainty.

8. Use different answers for different strengths when
   appropriate:
   - facts
   - completeness
   - relevance
   - tone
   - clarity
   - structure

9. Ties do not require blending.

10. Overall Score is for analytics only.

11. Follow all instructions in the original prompt.

12. Remove duplication.

13. Maintain one coherent voice.

14. Do not invent new important factual claims.


=========================================================
EVIDENCE AND CITATION RULES
=========================================================

The Evidence Packet contains source IDs.

Example:

Source ID 1
Source ID 2

When you use a specific current or verified factual
claim supported by an Evidence item, cite the source
immediately after the relevant sentence using:

[1]

or when multiple sources support the same claim:

[1][2]

Use ONLY source IDs that exist in the Evidence Packet.

Use a source ID only for a claim that the associated
Evidence item says it supports.

Do not invent citations.

Do not invent source numbers.

Do not include raw URLs in the answer.

Do not create a Sources section yourself.
The interface will create the source list separately.

For VERIFIED evidence:
You may state the supported fact normally and cite it.

For PARTIALLY_VERIFIED evidence:
Use cautious wording when the limitation matters.

For UNCERTAIN evidence:
Clearly flag the uncertainty if the claim is needed.

For CONFLICTED evidence:
Do not present one side as settled unless the Judge
explicitly resolved the conflict.

For NOT_CHECKED evidence:
Do not pretend it was verified.


=========================================================
FINAL OUTPUT
=========================================================

Return ONLY the final user-facing answer.

No explanation of the internal process.
"""


    response = (
        synthesis_client.responses.create(

            model=SYNTHESIS_MODEL,

            input=synthesis_prompt,

            max_output_tokens=2000
        )
    )


    final_answer = (
        response.output_text.strip()
    )


    if not final_answer:

        raise ValueError(
            "The Synthesis Agent returned no final answer."
        )


    return {

        "final_answer":
            final_answer,

        "model_used":
            SYNTHESIS_MODEL,

        "consensus":
            judgment.get(
                "agent_consensus",
                {}
            ).get(
                "level",
                "UNKNOWN"
            ),

        "sources":
            evidence_packet.get(
                "sources",
                []
            )
    }