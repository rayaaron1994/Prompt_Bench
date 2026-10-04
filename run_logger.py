import csv
import uuid

from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# CSV FILE
# =========================================================

CSV_PATH = Path(__file__).with_name(
    "prompt_bench_runs.csv"
)


# =========================================================
# HELPERS
# =========================================================

def get_metric_score(answer, metric):

    if not answer:
        return ""

    return (
        answer.get(metric, {})
        .get("score", "")
    )


def get_instruction_following(answer):

    if not answer:
        return ""

    return (
        answer.get(
            "instruction_following",
            {}
        ).get(
            "result",
            ""
        )
    )


# =========================================================
# LOG ONE COMPLETED PROMPT BENCH RUN
# =========================================================

def log_run(
    prompt,
    generation,
    judge_result,
    synthesis_result,
    final_result
):

    judgment = judge_result.get(
        "judgment",
        {}
    )

    provider_results = generation.get(
        "provider_results",
        {}
    )


    # =====================================================
    # JUDGE SCORES BY ANSWER ID
    # =====================================================

    answers_by_id = {
        answer.get("answer_id"): answer
        for answer in judgment.get("answers", [])
    }

    answer_a = answers_by_id.get("A", {})
    answer_b = answers_by_id.get("B", {})
    answer_c = answers_by_id.get("C", {})


    # =====================================================
    # FINAL QA DETAILS
    # =====================================================

    first_check = (
        final_result.get("first_check")
        or {}
    )

    second_check = (
        final_result.get("second_check")
        or {}
    )

    third_check = (
        final_result.get("third_check")
        or {}
    )

    final_check = (
        third_check
        if third_check
        else (
            second_check
            if second_check
            else first_check
        )
    )


    # =====================================================
    # BASE ROW
    # =====================================================

    row = {
        "run_id": uuid.uuid4().hex[:12],
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "prompt": " ".join(prompt.split()),

        "reporting_agent_count": judge_result.get(
            "reporting_agent_count",
            ""
        ),

        # A = OPENAI
        "a_provider": "OpenAI",
        "a_factual_accuracy": get_metric_score(
            answer_a,
            "factual_accuracy"
        ),
        "a_completeness": get_metric_score(
            answer_a,
            "completeness"
        ),
        "a_relevance": get_metric_score(
            answer_a,
            "relevance"
        ),
        "a_tone": get_metric_score(
            answer_a,
            "tone"
        ),
        "a_clarity": get_metric_score(
            answer_a,
            "clarity"
        ),
        "a_instruction_following": get_instruction_following(
            answer_a
        ),
        "a_overall_score": answer_a.get(
            "overall_score",
            ""
        ),

        # B = GEMINI
        "b_provider": "Gemini",
        "b_factual_accuracy": get_metric_score(
            answer_b,
            "factual_accuracy"
        ),
        "b_completeness": get_metric_score(
            answer_b,
            "completeness"
        ),
        "b_relevance": get_metric_score(
            answer_b,
            "relevance"
        ),
        "b_tone": get_metric_score(
            answer_b,
            "tone"
        ),
        "b_clarity": get_metric_score(
            answer_b,
            "clarity"
        ),
        "b_instruction_following": get_instruction_following(
            answer_b
        ),
        "b_overall_score": answer_b.get(
            "overall_score",
            ""
        ),

        # C = CLAUDE
        "c_provider": "Claude",
        "c_factual_accuracy": get_metric_score(
            answer_c,
            "factual_accuracy"
        ),
        "c_completeness": get_metric_score(
            answer_c,
            "completeness"
        ),
        "c_relevance": get_metric_score(
            answer_c,
            "relevance"
        ),
        "c_tone": get_metric_score(
            answer_c,
            "tone"
        ),
        "c_clarity": get_metric_score(
            answer_c,
            "clarity"
        ),
        "c_instruction_following": get_instruction_following(
            answer_c
        ),
        "c_overall_score": answer_c.get(
            "overall_score",
            ""
        ),

        # JUDGE / CONSENSUS
        "consensus_level": judgment.get(
            "agent_consensus",
            {}
        ).get(
            "level",
            ""
        ),
        "web_verification_used": judgment.get(
            "web_verification_used",
            False
        ),
        "factual_conflict_count": len(
            judgment.get(
                "factual_conflicts",
                []
            )
        ),

        # SYNTHESIS
        "synthesis_model": synthesis_result.get(
            "model_used",
            ""
        ),
        "source_count": len(
            synthesis_result.get(
                "sources",
                []
            )
        ),

        # FINAL QA
        "first_qa_status": first_check.get(
            "status",
            ""
        ),
        "second_qa_status": second_check.get(
            "status",
            ""
        ),
        "third_qa_status": third_check.get(
            "status",
            ""
        ),
        "final_qa_status": final_result.get(
            "status",
            ""
        ),
        "final_qa_issue_count": len(
            final_check.get(
                "issues",
                []
            )
        ),
        "revised": final_result.get(
            "revised",
            False
        ),
        "revision_count": final_result.get(
            "revision_count",
            0
        ),
        "qa_flags_remaining": final_result.get(
            "qa_flags_remaining",
            False
        ),
        "safe_to_show": final_result.get(
            "safe_to_show",
            False
        ),
        "used_source_count": len(
            final_result.get(
                "used_source_ids",
                []
            )
        )
    }


    # =====================================================
    # PROVIDER OPERATIONS
    # =====================================================

    for provider, prefix in [
        ("OpenAI", "openai"),
        ("Gemini", "gemini"),
        ("Claude", "claude")
    ]:

        result = provider_results.get(
            provider,
            {}
        )

        row[f"{prefix}_status"] = result.get(
            "status",
            ""
        )

        row[f"{prefix}_model"] = result.get(
            "model_used",
            ""
        )

        row[f"{prefix}_attempts"] = result.get(
            "attempts",
            ""
        )

        row[f"{prefix}_response_seconds"] = result.get(
            "response_time_seconds",
            ""
        )

        row[f"{prefix}_fallback_used"] = result.get(
            "fallback_used",
            False
        )

        row[f"{prefix}_error_code"] = result.get(
            "error_code",
            ""
        )


    # =====================================================
    # WRITE TO CSV
    # =====================================================

    file_exists = CSV_PATH.exists()

    with open(
        CSV_PATH,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(
                row.keys()
            )
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    return row["run_id"]
