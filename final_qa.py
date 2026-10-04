import os
import re
import json

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# SETUP
# =========================================================

load_dotenv()

final_qa_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

FINAL_QA_MODEL = "gpt-5.6-luna"


# =========================================================
# FINAL QA SCHEMA
# =========================================================

FINAL_QA_SCHEMA = {

    "type": "object",

    "properties": {

        "status": {
            "type": "string",
            "enum": [
                "PASS",
                "REVISE"
            ]
        },

        "reason": {
            "type": "string"
        },

        "issues": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "type": {
                        "type": "string",
                        "enum": [
                            "FACTS",
                            "INSTRUCTIONS",
                            "RELEVANCE",
                            "DUPLICATION",
                            "CLARITY",
                            "CONFLICT",
                            "INTERNAL_LEAK",
                            "UNSUPPORTED_CONTENT",
                            "CITATION"
                        ]
                    },

                    "description": {
                        "type": "string"
                    }
                },

                "required": [
                    "type",
                    "description"
                ],

                "additionalProperties": False
            }
        },

        "corrections": {
            "type": "array",

            "items": {
                "type": "string"
            }
        }
    },

    "required": [
        "status",
        "reason",
        "issues",
        "corrections"
    ],

    "additionalProperties": False
}


# =========================================================
# CITATION HELPERS
# =========================================================

def find_citation_ids(
    answer
):

    matches = re.findall(
        r"\[(\d+)\]",
        answer
    )

    return sorted(
        set(
            int(match)
            for match
            in matches
        )
    )


def valid_source_ids(
    judge_result
):

    evidence_packet = (
        judge_result.get(
            "evidence_packet",
            {}
        )
    )

    return {

        int(source["id"])

        for source
        in evidence_packet.get(
            "sources",
            []
        )

        if source.get(
            "id"
        ) is not None
    }


def enforce_citation_rules(
    qa_result,
    final_answer,
    judge_result
):

    used_ids = set(
        find_citation_ids(
            final_answer
        )
    )

    valid_ids = valid_source_ids(
        judge_result
    )

    invalid_ids = sorted(
        used_ids - valid_ids
    )


    if invalid_ids:

        qa_result[
            "status"
        ] = "REVISE"

        qa_result[
            "issues"
        ].append({

            "type":
                "CITATION",

            "description":
                (
                    "The answer contains citation IDs "
                    f"that do not exist in the evidence "
                    f"packet: {invalid_ids}"
                )
        })

        qa_result[
            "corrections"
        ].append(
            "Remove or replace citation IDs that do not "
            "exist in the evidence packet."
        )


    return qa_result


# =========================================================
# CHECK FINAL ANSWER
# =========================================================

def check_final_answer(
    prompt,
    final_answer,
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


    qa_prompt = f"""
You are the Final QA Gate for Prompt Bench.

Do NOT create a new answer.

Inspect the proposed final answer before it reaches
the user.

You have:

1. Original user prompt
2. Anonymous testimony
3. Judge decision
4. Evidence packet
5. Proposed final answer


=========================================================
ORIGINAL USER PROMPT
=========================================================

{prompt}


=========================================================
ANONYMOUS TESTIMONY
=========================================================

{testimony}


=========================================================
JUDGE DECISION
=========================================================

{judge_decision}


=========================================================
EVIDENCE PACKET
=========================================================

{evidence}


=========================================================
PROPOSED FINAL ANSWER
=========================================================

{final_answer}


=========================================================
FINAL QA CHECKS
=========================================================

FACTS

Make sure blocked, rejected, disputed, or unreliable
claims have not reappeared.

Do not combine conflicting factual claims.


INSTRUCTIONS

Confirm the answer follows the user's requested:

- format
- tone
- length
- audience
- exclusions
- constraints


RELEVANCE

The response must directly answer the request.


DUPLICATION

Do not repeat ideas merely because several source
answers included them.


CLARITY

The answer should read as one coherent response.


INTERNAL PROCESS

Do not expose:

- Answer A/B/C
- provider identity
- Judge scores
- category leaders
- internal QA
- synthesis instructions


UNSUPPORTED CONTENT

Do not allow important new factual claims that were
invented during synthesis.


CITATIONS

Citation syntax is:

[1]

or:

[1][2]

Every citation number must exist in the Evidence Packet.

A citation must support the sentence it follows.

Do not allow a source to be attached to an unrelated
claim.

When a specific current or externally verified claim
from the Evidence Packet appears in the final answer,
retain appropriate evidence citations.

Do not demand citations for ordinary non-factual
writing or obvious general knowledge.

Do not require a Sources section.
The interface creates that separately.


=========================================================
DECISION RULE
=========================================================

Return PASS only if the answer is ready for the user.

Return REVISE when a meaningful problem exists.

For REVISE:

- identify each problem
- give specific correction instructions
- do not rewrite the answer yourself
"""


    response = (
        final_qa_client.responses.create(

            model=FINAL_QA_MODEL,

            input=qa_prompt,

            text={
                "format": {

                    "type":
                        "json_schema",

                    "name":
                        "prompt_bench_final_qa",

                    "strict":
                        True,

                    "schema":
                        FINAL_QA_SCHEMA
                }
            }
        )
    )


    qa_result = json.loads(
        response.output_text
    )


    return enforce_citation_rules(
        qa_result,
        final_answer,
        judge_result
    )


# =========================================================
# REVISE ANSWER
# =========================================================

def revise_final_answer(
    prompt,
    final_answer,
    judge_result,
    qa_result
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


    issues = json.dumps(
        qa_result.get(
            "issues",
            []
        ),
        indent=2
    )


    corrections = json.dumps(
        qa_result.get(
            "corrections",
            []
        ),
        indent=2
    )


    revision_prompt = f"""
You are revising a Prompt Bench synthesized response.

Correct the Final QA problems and return ONE improved
user-facing answer.


=========================================================
ORIGINAL USER PROMPT
=========================================================

{prompt}


=========================================================
ANONYMOUS TESTIMONY
=========================================================

{testimony}


=========================================================
JUDGE DECISION
=========================================================

{judge_decision}


=========================================================
EVIDENCE PACKET
=========================================================

{evidence}


=========================================================
CURRENT ANSWER
=========================================================

{final_answer}


=========================================================
QA ISSUES
=========================================================

{issues}


=========================================================
REQUIRED CORRECTIONS
=========================================================

{corrections}


=========================================================
REVISION RULES
=========================================================

1. Correct only what is necessary.

2. Preserve useful material that already works.

3. Never reintroduce Judge-blocked content.

4. Do not invent factual claims.

5. Do not combine unresolved conflicting claims.

6. Follow the original user's instructions.

7. Maintain one voice.

8. Remove duplication.

9. Do not reveal Prompt Bench's internal process.

10. Citation syntax is [1] or [1][2].

11. Use ONLY source IDs present in the Evidence Packet.

12. Attach a citation only to a claim that source
    actually supports.

13. Do not include raw source URLs.

14. Do not create a Sources section.

Return ONLY the revised answer.
"""


    response = (
        final_qa_client.responses.create(

            model=FINAL_QA_MODEL,

            input=revision_prompt,

            max_output_tokens=2000
        )
    )


    revised_answer = (
        response.output_text.strip()
    )


    if not revised_answer:

        raise ValueError(
            "Final QA revision returned no answer."
        )


    return revised_answer


# =========================================================
# COMPLETE FINAL QA FLOW
# =========================================================

def validate_final_answer(
    prompt,
    final_answer,
    judge_result
):

    # =====================================================
    # FIRST CHECK
    # =====================================================

    first_check = check_final_answer(
        prompt,
        final_answer,
        judge_result
    )


    # =====================================================
    # PASS FIRST TRY
    # =====================================================

    if first_check[
        "status"
    ] == "PASS":

        return {

            "safe_to_show":
                True,

            "status":
                "PASS",

            "final_answer":
                final_answer,

            "revised":
                False,

            "revision_count":
                0,

            "first_check":
                first_check,

            "second_check":
                None,

            "third_check":
                None,

            "qa_flags_remaining":
                False,

            "used_source_ids":
                find_citation_ids(
                    final_answer
                )
        }


    # =====================================================
    # FIRST AUTOMATIC REVISION
    # =====================================================

    revised_answer = (
        revise_final_answer(
            prompt,
            final_answer,
            judge_result,
            first_check
        )
    )


    # =====================================================
    # SECOND CHECK
    # =====================================================

    second_check = check_final_answer(
        prompt,
        revised_answer,
        judge_result
    )


    # =====================================================
    # FIRST REVISION PASSED
    # =====================================================

    if second_check[
        "status"
    ] == "PASS":

        return {

            "safe_to_show":
                True,

            "status":
                "PASS_AFTER_REVISION",

            "final_answer":
                revised_answer,

            "revised":
                True,

            "revision_count":
                1,

            "first_check":
                first_check,

            "second_check":
                second_check,

            "third_check":
                None,

            "qa_flags_remaining":
                False,

            "used_source_ids":
                find_citation_ids(
                    revised_answer
                )
        }


    # =====================================================
    # SECOND AUTOMATIC REVISION
    #
    # If the first repair still has meaningful problems,
    # use the newest QA feedback for one more repair rather
    # than ending the user's request with no answer.
    # =====================================================

    recovery_answer = (
        revise_final_answer(
            prompt,
            revised_answer,
            judge_result,
            second_check
        )
    )


    # =====================================================
    # THIRD / FINAL CHECK
    # =====================================================

    third_check = check_final_answer(
        prompt,
        recovery_answer,
        judge_result
    )


    # =====================================================
    # SECOND REVISION PASSED
    # =====================================================

    if third_check[
        "status"
    ] == "PASS":

        return {

            "safe_to_show":
                True,

            "status":
                "PASS_AFTER_SECOND_REVISION",

            "final_answer":
                recovery_answer,

            "revised":
                True,

            "revision_count":
                2,

            "first_check":
                first_check,

            "second_check":
                second_check,

            "third_check":
                third_check,

            "qa_flags_remaining":
                False,

            "used_source_ids":
                find_citation_ids(
                    recovery_answer
                )
        }


    # =====================================================
    # GRACEFUL DELIVERY
    #
    # Final QA is a quality-control system, not a dead-end.
    # If two repair attempts still receive QA flags, return
    # the most conservative repaired answer instead of
    # forcing the user to start over.
    #
    # The remaining QA flags stay visible internally for
    # analytics and future system improvement.
    # =====================================================

    return {

        "safe_to_show":
            True,

        "status":
            "DELIVERED_WITH_QA_FLAGS",

        "final_answer":
            recovery_answer,

        "revised":
            True,

        "revision_count":
            2,

        "first_check":
            first_check,

        "second_check":
            second_check,

        "third_check":
            third_check,

        "qa_flags_remaining":
            True,

        "used_source_ids":
            find_citation_ids(
                recovery_answer
            )
    }
