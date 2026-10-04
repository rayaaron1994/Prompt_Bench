import os
import json
import random

from pathlib import Path
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# SETUP
# =========================================================

load_dotenv()

judge_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

JUDGE_MODEL = "gpt-5.6-luna"

RUBRIC_PATH = Path(__file__).with_name(
    "JUDGE_RUBRIC.md"
)

with open(
    RUBRIC_PATH,
    "r",
    encoding="utf-8"
) as file:
    JUDGE_RUBRIC = file.read()


# =========================================================
# BLIND PROVIDER IDENTITIES
# =========================================================

def anonymize_answers(provider_answers):

    items = list(
        provider_answers.items()
    )

    random.shuffle(items)

    labels = [
        "A",
        "B",
        "C"
    ]

    anonymous_answers = {}
    provider_map = {}

    for label, (provider, answer) in zip(
        labels,
        items
    ):

        anonymous_answers[label] = answer
        provider_map[label] = provider

    return (
        anonymous_answers,
        provider_map
    )


# =========================================================
# ANALYTICS SCORE
# =========================================================

def calculate_overall_score(scores):

    overall = (
        scores["factual_accuracy"] * 0.30
        + scores["completeness"] * 0.20
        + scores["relevance"] * 0.20
        + scores["tone"] * 0.15
        + scores["clarity"] * 0.15
    )

    return round(
        overall,
        2
    )


# =========================================================
# SCHEMA HELPERS
# =========================================================

def metric_schema():

    return {
        "type": "object",

        "properties": {

            "score": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5
            },

            "reason": {
                "type": "string"
            }
        },

        "required": [
            "score",
            "reason"
        ],

        "additionalProperties": False
    }


def build_judge_schema(answer_ids):

    answer_id_schema = {
        "type": "string",
        "enum": answer_ids
    }

    return {
        "type": "object",

        "properties": {

            # =================================================
            # INDIVIDUAL ANSWER EVALUATIONS
            # =================================================

            "answers": {
                "type": "array",

                "items": {
                    "type": "object",

                    "properties": {

                        "answer_id": answer_id_schema,

                        "factual_accuracy":
                            metric_schema(),

                        "completeness":
                            metric_schema(),

                        "relevance":
                            metric_schema(),

                        "tone":
                            metric_schema(),

                        "clarity":
                            metric_schema(),

                        "instruction_following": {
                            "type": "object",

                            "properties": {

                                "result": {
                                    "type": "string",
                                    "enum": [
                                        "PASS",
                                        "PARTIAL",
                                        "FAIL"
                                    ]
                                },

                                "reason": {
                                    "type": "string"
                                }
                            },

                            "required": [
                                "result",
                                "reason"
                            ],

                            "additionalProperties": False
                        },

                        "best_use": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },

                        "do_not_use": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },

                    "required": [
                        "answer_id",
                        "factual_accuracy",
                        "completeness",
                        "relevance",
                        "tone",
                        "clarity",
                        "instruction_following",
                        "best_use",
                        "do_not_use"
                    ],

                    "additionalProperties": False
                }
            },

            # =================================================
            # CONSENSUS
            # =================================================

            "agent_consensus": {
                "type": "object",

                "properties": {

                    "level": {
                        "type": "string",
                        "enum": [
                            "HIGH",
                            "MAJORITY",
                            "LIMITED",
                            "LOW"
                        ]
                    },

                    "reason": {
                        "type": "string"
                    }
                },

                "required": [
                    "level",
                    "reason"
                ],

                "additionalProperties": False
            },

            # =================================================
            # CATEGORY LEADERS
            # =================================================

            "category_leaders": {
                "type": "object",

                "properties": {

                    "factual_accuracy": {
                        "type": "array",
                        "items": answer_id_schema
                    },

                    "completeness": {
                        "type": "array",
                        "items": answer_id_schema
                    },

                    "relevance": {
                        "type": "array",
                        "items": answer_id_schema
                    },

                    "tone": {
                        "type": "array",
                        "items": answer_id_schema
                    },

                    "clarity": {
                        "type": "array",
                        "items": answer_id_schema
                    }
                },

                "required": [
                    "factual_accuracy",
                    "completeness",
                    "relevance",
                    "tone",
                    "clarity"
                ],

                "additionalProperties": False
            },

            # =================================================
            # FACTUAL CONFLICTS
            # =================================================

            "factual_conflicts": {
                "type": "array",

                "items": {
                    "type": "string"
                }
            },

            # =================================================
            # SYNTHESIS GUIDANCE
            # =================================================

            "synthesis_guidance": {
                "type": "array",

                "items": {
                    "type": "string"
                }
            },

            # =================================================
            # WEB VERIFICATION
            # =================================================

            "web_verification_used": {
                "type": "boolean"
            },

            # =================================================
            # EVIDENCE
            # =================================================

            "evidence": {
                "type": "array",

                "items": {
                    "type": "object",

                    "properties": {

                        "claim": {
                            "type": "string"
                        },

                        "status": {
                            "type": "string",
                            "enum": [
                                "VERIFIED",
                                "PARTIALLY_VERIFIED",
                                "UNCERTAIN",
                                "CONFLICTED",
                                "NOT_CHECKED"
                            ]
                        },

                        "source_urls": {
                            "type": "array",

                            "items": {
                                "type": "string"
                            }
                        },

                        "note": {
                            "type": "string"
                        }
                    },

                    "required": [
                        "claim",
                        "status",
                        "source_urls",
                        "note"
                    ],

                    "additionalProperties": False
                }
            }
        },

        "required": [
            "answers",
            "agent_consensus",
            "category_leaders",
            "factual_conflicts",
            "synthesis_guidance",
            "web_verification_used",
            "evidence"
        ],

        "additionalProperties": False
    }


# =========================================================
# URL HELPERS
# =========================================================

def normalize_url(url):

    if not url:
        return None

    try:

        parsed = urlparse(
            str(url).strip()
        )

        if parsed.scheme not in [
            "http",
            "https"
        ]:
            return None

        path = (
            parsed.path.rstrip("/")
            or "/"
        )

        cleaned = parsed._replace(
            path=path,
            fragment=""
        )

        return urlunparse(
            cleaned
        )

    except Exception:

        return None


def url_without_query(url):

    normalized = normalize_url(
        url
    )

    if not normalized:
        return None

    parsed = urlparse(
        normalized
    )

    cleaned = parsed._replace(
        query="",
        fragment=""
    )

    return urlunparse(
        cleaned
    )


def fallback_source_title(url):

    try:

        hostname = urlparse(
            url
        ).hostname

        if hostname:

            return hostname.replace(
                "www.",
                ""
            )

    except Exception:

        pass

    return "Web source"


# =========================================================
# EXTRACT REAL WEB SOURCES
# =========================================================

def extract_web_sources(response):
    """
    Extracts URLs that actually appeared in OpenAI's
    web-search response/tool activity.

    URLs typed only inside the Judge's JSON are not
    automatically trusted.
    """

    dumped = response.model_dump()

    sources = {}

    web_search_used = False


    # -----------------------------------------------------
    # ADD SOURCE
    # -----------------------------------------------------

    def add_source(
        url,
        title=None
    ):

        normalized = normalize_url(
            url
        )

        if not normalized:

            return


        existing = sources.get(
            normalized
        )


        source_title = (
            title
            or fallback_source_title(
                normalized
            )
        )


        if existing:

            if (
                not existing.get("title")
                or existing["title"]
                == fallback_source_title(
                    normalized
                )
            ):

                existing[
                    "title"
                ] = source_title

            return


        sources[
            normalized
        ] = {

            "url":
                normalized,

            "title":
                source_title
        }


    # -----------------------------------------------------
    # RECURSIVELY SEARCH RESPONSE
    # -----------------------------------------------------

    def walk(value):

        nonlocal web_search_used


        if isinstance(
            value,
            dict
        ):

            item_type = value.get(
                "type"
            )


            # =============================================
            # URL CITATION
            # =============================================

            if item_type == "url_citation":

                add_source(
                    value.get(
                        "url"
                    ),
                    value.get(
                        "title"
                    )
                )


            # =============================================
            # WEB SEARCH TOOL CALL
            # =============================================

            if item_type == "web_search_call":

                web_search_used = True

                # FIX:
                # action can sometimes be None
                action = (
                    value.get("action")
                    or {}
                )


                if isinstance(
                    action,
                    dict
                ):

                    # FIX:
                    # sources can sometimes be None
                    action_sources = (
                        action.get("sources")
                        or []
                    )


                    for source in action_sources:

                        if isinstance(
                            source,
                            dict
                        ):

                            add_source(
                                source.get(
                                    "url"
                                ),
                                source.get(
                                    "title"
                                )
                            )


                    # Some web-search actions may contain
                    # a directly opened page URL.
                    action_url = action.get(
                        "url"
                    )


                    if action_url:

                        add_source(
                            action_url
                        )


            # =============================================
            # RECURSE THROUGH CHILD VALUES
            # =============================================

            for child in value.values():

                walk(
                    child
                )


        elif isinstance(
            value,
            list
        ):

            for child in value:

                walk(
                    child
                )


    walk(
        dumped
    )


    return (
        web_search_used,
        sources
    )


# =========================================================
# MATCH JUDGE URL TO ACTUAL SEARCH URL
# =========================================================

def match_real_source(
    requested_url,
    real_sources
):

    normalized = normalize_url(
        requested_url
    )


    if not normalized:

        return None


    # -----------------------------------------------------
    # EXACT NORMALIZED MATCH
    # -----------------------------------------------------

    if normalized in real_sources:

        return real_sources[
            normalized
        ]


    # -----------------------------------------------------
    # IGNORE QUERY STRING AS FALLBACK
    # -----------------------------------------------------

    requested_base = url_without_query(
        normalized
    )

    matches = []


    for real_url, source in (
        real_sources.items()
    ):

        if (
            url_without_query(
                real_url
            )
            == requested_base
        ):

            matches.append(
                source
            )


    if len(matches) == 1:

        return matches[
            0
        ]


    return None


# =========================================================
# BUILD SAFE EVIDENCE PACKET
# =========================================================

def build_evidence_packet(
    judgment,
    web_search_used,
    real_sources
):

    evidence_items = []

    used_sources = {}


    # FIX:
    # evidence may technically come back as None
    judgment_evidence = (
        judgment.get("evidence")
        or []
    )


    for item in judgment_evidence:

        if not isinstance(
            item,
            dict
        ):

            continue


        safe_sources = []

        seen_urls = set()


        # FIX:
        # source_urls may also be None
        requested_urls = (
            item.get("source_urls")
            or []
        )


        for requested_url in requested_urls:

            matched = match_real_source(
                requested_url,
                real_sources
            )


            if not matched:

                continue


            url = matched[
                "url"
            ]


            if url in seen_urls:

                continue


            seen_urls.add(
                url
            )


            safe_sources.append(
                matched
            )


            used_sources[
                url
            ] = matched


        status = item.get(
            "status",
            "NOT_CHECKED"
        )


        note = item.get(
            "note",
            ""
        ) or ""


        # =================================================
        # ENFORCE TWO-SOURCE STANDARD
        # =================================================

        if (
            status == "VERIFIED"
            and len(safe_sources) < 2
        ):

            status = (
                "PARTIALLY_VERIFIED"
                if safe_sources
                else "UNCERTAIN"
            )


            extra_note = (
                "Prompt Bench could not confirm "
                "the normal two-source verification "
                "threshold from the captured web evidence."
            )


            note = (
                f"{note} {extra_note}"
            ).strip()


        evidence_items.append({

            "claim":
                item.get(
                    "claim",
                    ""
                )
                or "",

            "status":
                status,

            "source_urls": [
                source["url"]

                for source
                in safe_sources
            ],

            "note":
                note
        })


    # =====================================================
    # CREATE SOURCE CATALOG
    # =====================================================

    source_catalog = []

    source_id_map = {}


    for index, (
        url,
        source
    ) in enumerate(

        used_sources.items(),

        start=1
    ):

        source_id_map[
            url
        ] = index


        source_catalog.append({

            "id":
                index,

            "title":
                source.get(
                    "title"
                )
                or fallback_source_title(
                    url
                ),

            "url":
                url
        })


    # =====================================================
    # ADD SOURCE IDS TO EVIDENCE ITEMS
    # =====================================================

    for item in evidence_items:

        item[
            "source_ids"
        ] = [

            source_id_map[
                url
            ]

            for url
            in item[
                "source_urls"
            ]

            if url
            in source_id_map
        ]


    return {

        "web_verification_used":
            web_search_used,

        "items":
            evidence_items,

        "sources":
            source_catalog
    }


# =========================================================
# THE JUDGE
# =========================================================

def judge_answers(
    prompt,
    provider_answers
):

    reporting_agent_count = len(
        provider_answers
    )


    # =====================================================
    # REQUIRE AT LEAST TWO RESPONSES
    # =====================================================

    if reporting_agent_count == 0:

        raise ValueError(
            "No agents reported to the bench."
        )


    if reporting_agent_count == 1:

        raise ValueError(
            "Only one agent reported to the bench. "
            "At least two responses are required."
        )


    # =====================================================
    # ANONYMIZE PROVIDERS
    # =====================================================

    (
        anonymous_answers,
        provider_map

    ) = anonymize_answers(
        provider_answers
    )


    answer_ids = list(
        anonymous_answers.keys()
    )


    testimony = "\n\n".join(

        f"ANSWER {answer_id}:\n{answer}"

        for answer_id, answer
        in anonymous_answers.items()
    )


    # =====================================================
    # JUDGE PROMPT
    # =====================================================

    judge_prompt = f"""
You are the QA Judge for Prompt Bench.

You are reviewing anonymous testimony from multiple
AI systems responding to the same user request.

The provider identities have intentionally been hidden.

There are currently {reporting_agent_count}
agents reporting to the bench.

Never guess provider identity.

Do NOT choose one overall winner.


=========================================================
ORIGINAL USER PROMPT
=========================================================

{prompt}


=========================================================
ANONYMOUS TESTIMONY
=========================================================

{testimony}


=========================================================
PROMPT BENCH JUDGE RUBRIC
=========================================================

{JUDGE_RUBRIC}


=========================================================
CORE JUDGING RULES
=========================================================

1. Evaluate each answer independently first.

2. Score:
   - Factual Accuracy
   - Completeness
   - Relevance
   - Tone
   - Clarity

3. Evaluate Instruction Following separately.

4. Apply the Prompt Bench cross-metric rules.

5. Do NOT select one overall winner.

6. Identify category leaders.

7. Ties are allowed.

8. Apply the Prompt Bench tie rules.

9. Weak factual accuracy does not automatically block
   non-factual strengths such as tone or structure.

10. Unsupported or incorrect factual claims must not
    be recommended for synthesis.

11. Best Use describes safe reusable strengths.

12. Do Not Use describes material that must be blocked.

13. Identify meaningful factual conflicts.

14. Agent agreement is NOT proof.

15. Keep score explanations short and specific.


=========================================================
WEB VERIFICATION RULES
=========================================================

Use web search when the response contains important
claims that are:

- current
- specific
- questionable
- disputed
- time-sensitive
- central to the user's decision

Do not waste searches on obvious facts.

For important factual claims, the normal verification
standard is two strong independent sources.

Use three or more when the claim is high-stakes,
controversial, disputed, or when strong sources conflict.

Prefer:

1. primary or official sources
2. original research or original datasets
3. strong independent secondary sources

Sites repeating the same original source do not count
as independent confirmation.

For every important factual claim you actually check,
create an Evidence item.

Evidence status meanings:

VERIFIED:
Strong evidence supports the claim and the normal
source threshold was met.

PARTIALLY_VERIFIED:
Some evidence supports the claim but verification
is incomplete.

UNCERTAIN:
Evidence is weak, incomplete, stale, or insufficient.

CONFLICTED:
Strong sources materially disagree.

NOT_CHECKED:
The claim was not important enough to verify.

When web verification is used, put the exact URLs
from your web research into source_urls.

Never invent a source URL.

If sources disagree, preserve the uncertainty instead
of forcing a conclusion.


=========================================================
CONSENSUS RULES
=========================================================

HIGH:
All three agents reported and substantially agree.

MAJORITY:
All three reported and two substantially agree.

LIMITED:
Only two agents reported.

LOW:
Available testimony materially disagrees or support
is weak.

HIGH is impossible unless all three agents reported.

If only two agents reported, never return HIGH
or MAJORITY.
"""


    # =====================================================
    # RUN JUDGE
    # =====================================================

    response = judge_client.responses.create(

        model=JUDGE_MODEL,

        input=judge_prompt,

        tools=[
            {
                "type": "web_search"
            }
        ],

        # Explicitly request consulted web sources
        include=[
            "web_search_call.action.sources"
        ],

        text={
            "format": {

                "type":
                    "json_schema",

                "name":
                    "prompt_bench_judgment",

                "strict":
                    True,

                "schema":
                    build_judge_schema(
                        answer_ids
                    )
            }
        }
    )


    # =====================================================
    # PARSE JUDGE RESPONSE
    # =====================================================

    judgment = json.loads(
        response.output_text
    )


    # =====================================================
    # CAPTURE REAL WEB SOURCES
    # =====================================================

    (
        web_search_used,
        real_sources

    ) = extract_web_sources(
        response
    )


    judgment[
        "web_verification_used"
    ] = web_search_used


    # =====================================================
    # BUILD SAFE EVIDENCE PACKET
    # =====================================================

    evidence_packet = (
        build_evidence_packet(
            judgment,
            web_search_used,
            real_sources
        )
    )


    # =====================================================
    # ENFORCE AVAILABILITY-AWARE CONSENSUS
    # =====================================================

    if reporting_agent_count == 2:

        judgment[
            "agent_consensus"
        ][
            "level"
        ] = "LIMITED"


        existing_reason = (
            judgment[
                "agent_consensus"
            ].get(
                "reason",
                ""
            )
            or ""
        )


        judgment[
            "agent_consensus"
        ][
            "reason"
        ] = (
            "Only two agents reported to the bench. "
            "Full three-agent consensus could not be "
            f"established. {existing_reason}"
        ).strip()


    # =====================================================
    # ANALYTICS-ONLY OVERALL SCORES
    # =====================================================

    for answer in (
        judgment.get(
            "answers"
        )
        or []
    ):

        scores = {

            "factual_accuracy":
                answer[
                    "factual_accuracy"
                ][
                    "score"
                ],

            "completeness":
                answer[
                    "completeness"
                ][
                    "score"
                ],

            "relevance":
                answer[
                    "relevance"
                ][
                    "score"
                ],

            "tone":
                answer[
                    "tone"
                ][
                    "score"
                ],

            "clarity":
                answer[
                    "clarity"
                ][
                    "score"
                ]
        }


        answer[
            "overall_score"
        ] = calculate_overall_score(
            scores
        )


    # =====================================================
    # RETURN INTERNAL BENCH RESULT
    # =====================================================

    return {

        "judgment":
            judgment,

        "reporting_agent_count":
            reporting_agent_count,

        # Provider mapping stays hidden from Judge
        "provider_map":
            provider_map,

        # Anonymous testimony Judge actually saw
        "anonymous_answers":
            anonymous_answers,

        # Verified/captured web evidence for
        # Synthesis + Final QA + user citations
        "evidence_packet":
            evidence_packet
    }