import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from google import genai
from google.genai import types


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# CREATE API CLIENTS
# =========================================================

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

claude_client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# =========================================================
# MODEL SETTINGS
# =========================================================

OPENAI_MODEL = "gpt-5.6-luna"
CLAUDE_MODEL = "claude-sonnet-5"

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_FALLBACK_MODEL = "gemini-3.5-flash-lite"

# Gemini gets its own recovery path so we do not stack our
# retry loop on top of the Google SDK's built-in retries.
GEMINI_RECOVERY_CODES = {408, 429, 500, 502, 503, 504}
GEMINI_FALLBACK_DELAY_SECONDS = 2

MAX_RETRIES = 3

RETRYABLE_CODES = {
    408,
    429,
    500,
    502,
    503,
    504
}


# =========================================================
# ERROR HELPERS
# =========================================================

def get_error_code(error):
    """
    Attempts to extract an HTTP error code from
    OpenAI, Anthropic, or Google SDK errors.
    """

    # Some SDKs expose status_code directly
    status_code = getattr(error, "status_code", None)

    if status_code is not None:
        try:
            return int(status_code)
        except (TypeError, ValueError):
            pass

    # Google errors may expose .code
    code = getattr(error, "code", None)

    if code is not None:
        try:
            return int(code)
        except (TypeError, ValueError):
            pass

    # Some errors contain a response object
    response = getattr(error, "response", None)

    if response is not None:
        response_status = getattr(response, "status_code", None)

        if response_status is not None:
            try:
                return int(response_status)
            except (TypeError, ValueError):
                pass

    # Final backup:
    # look for a common HTTP code in the error text
    match = re.search(
        r"\b(401|403|404|408|409|429|500|502|503|504)\b",
        str(error)
    )

    if match:
        return int(match.group(1))

    return None


def describe_error(error_code):
    """
    Human-readable technical description
    for the Prompt Bench courtroom UI.
    """

    descriptions = {
        401: "credentials rejected",
        403: "provider access denied",
        404: "requested model or resource not found",
        408: "provider request timed out",
        429: "provider rate limit reached",
        500: "provider internal error",
        502: "provider gateway error",
        503: "provider temporarily unavailable",
        504: "provider gateway timeout"
    }

    return descriptions.get(
        error_code,
        "provider error"
    )


def court_message(error_code, retrying=False):
    """
    Creates Prompt Bench's courtroom-themed
    provider status message.
    """

    description = describe_error(error_code)

    if retrying:

        if error_code:
            return (
                "Agent is delayed in chambers. "
                f"Court code: {error_code} — {description}. "
                "Retrying..."
            )

        return (
            "Agent is delayed in chambers. "
            "The provider is temporarily unavailable. "
            "Retrying..."
        )

    if error_code:
        return (
            "Agent failed to appear. "
            f"Court code: {error_code} — {description}. "
            "The bench will proceed without this testimony."
        )

    return (
        "Agent failed to appear. "
        "The bench will proceed without this testimony."
    )


# =========================================================
# GENERIC PROVIDER RETRY SYSTEM
# =========================================================

def run_with_retries(provider_name, request_function):
    """
    Runs a provider request safely.

    Temporary errors are retried.

    If the provider still fails, Prompt Bench marks
    that provider unavailable instead of crashing
    or giving the provider a bad QA score.
    """

    start_time = time.perf_counter()

    last_error = None
    last_error_code = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            result = request_function()

            response_time = round(
                time.perf_counter() - start_time,
                2
            )

            return {
                "provider": provider_name,
                "status": "available",
                "answer": result["answer"],
                "model_used": result["model_used"],
                "fallback_used": result.get(
                    "fallback_used",
                    False
                ),
                "fallback_reason_code": result.get(
                    "fallback_reason_code"
                ),
                "error_code": None,
                "error_message": None,
                "court_message": None,
                "attempts": attempt,
                "response_time_seconds": response_time
            }

        except Exception as error:

            last_error = error
            last_error_code = get_error_code(error)

            retryable = (
                last_error_code in RETRYABLE_CODES
            )

            # Retry temporary provider problems
            if retryable and attempt < MAX_RETRIES:

                print(
                    f"{provider_name}: "
                    f"{court_message(last_error_code, retrying=True)}"
                )

                # Exponential backoff:
                # first failure = 1 second
                # second failure = 2 seconds
                time.sleep(2 ** (attempt - 1))

                continue

            # Stop immediately for errors that
            # probably will not fix themselves.
            response_time = round(
                time.perf_counter() - start_time,
                2
            )

            return {
                "provider": provider_name,
                "status": "unavailable",
                "answer": None,
                "model_used": None,
                "fallback_used": False,
                "fallback_reason_code": None,
                "error_code": last_error_code,
                "error_message": str(last_error),
                "court_message": court_message(
                    last_error_code,
                    retrying=False
                ),
                "attempts": attempt,
                "response_time_seconds": response_time
            }

    # Safety fallback.
    # The code should normally never reach here.

    response_time = round(
        time.perf_counter() - start_time,
        2
    )

    return {
        "provider": provider_name,
        "status": "unavailable",
        "answer": None,
        "model_used": None,
        "fallback_used": False,
        "fallback_reason_code": None,
        "error_code": last_error_code,
        "error_message": str(last_error),
        "court_message": court_message(
            last_error_code,
            retrying=False
        ),
        "attempts": MAX_RETRIES,
        "response_time_seconds": response_time
    }


# =========================================================
# OPENAI AGENT
# =========================================================

def ask_openai(prompt):

    response = openai_client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
        max_output_tokens=1200
    )

    answer = response.output_text

    if not answer:
        raise ValueError(
            "OpenAI returned no text."
        )

    return {
        "answer": answer,
        "model_used": OPENAI_MODEL,
        "fallback_used": False,
        "fallback_reason_code": None
    }


# =========================================================
# CLAUDE AGENT
# =========================================================

def ask_claude(prompt):

    response = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1200,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    text_blocks = []

    for block in response.content:

        if getattr(block, "type", None) == "text":

            text = getattr(
                block,
                "text",
                ""
            )

            if text:
                text_blocks.append(text)

    answer = "\n".join(
        text_blocks
    ).strip()

    if not answer:
        raise ValueError(
            "Claude returned no text."
        )

    return {
        "answer": answer,
        "model_used": CLAUDE_MODEL,
        "fallback_used": False,
        "fallback_reason_code": None
    }


# =========================================================
# GEMINI AGENT
# =========================================================

def call_gemini_model(model_name, prompt):
    """
    Sends one logical request to a Gemini model.

    The Google SDK already performs its own transient-error
    retries, so Prompt Bench does not wrap Gemini in the
    generic retry loop as well.
    """

    response = gemini_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=1200
        )
    )

    answer = response.text

    if not answer:
        raise ValueError(
            f"{model_name} returned no text."
        )

    return answer


def run_gemini(prompt):
    """
    Gemini-specific recovery path.

    1. Try Gemini 3.8 Flash.
    2. If the primary model hits a transient error such as
       429 or 503, wait briefly and call a lighter fallback.
    3. If the fallback also fails, mark Gemini unavailable.

    This avoids retry multiplication between Prompt Bench
    and the Google SDK while preserving provider-failure
    resilience for the rest of the pipeline.
    """

    start_time = time.perf_counter()

    try:
        answer = call_gemini_model(
            GEMINI_MODEL,
            prompt
        )

        response_time = round(
            time.perf_counter() - start_time,
            2
        )

        return {
            "provider": "Gemini",
            "status": "available",
            "answer": answer,
            "model_used": GEMINI_MODEL,
            "fallback_used": False,
            "fallback_reason_code": None,
            "error_code": None,
            "error_message": None,
            "court_message": None,
            "attempts": 1,
            "response_time_seconds": response_time
        }

    except Exception as primary_error:
        primary_error_code = get_error_code(
            primary_error
        )

        # Authentication, permissions, model-not-found, and
        # other non-transient errors should fail fast.
        if primary_error_code not in GEMINI_RECOVERY_CODES:

            response_time = round(
                time.perf_counter() - start_time,
                2
            )

            return {
                "provider": "Gemini",
                "status": "unavailable",
                "answer": None,
                "model_used": None,
                "fallback_used": False,
                "fallback_reason_code": None,
                "error_code": primary_error_code,
                "error_message": str(primary_error),
                "court_message": court_message(
                    primary_error_code,
                    retrying=False
                ),
                "attempts": 1,
                "response_time_seconds": response_time
            }

        description = describe_error(
            primary_error_code
        )

        print(
            "Gemini: Agent is delayed in chambers. "
            f"Court code: {primary_error_code} — {description}. "
            "Calling alternate chambers..."
        )

        time.sleep(
            GEMINI_FALLBACK_DELAY_SECONDS
        )

        try:
            fallback_answer = call_gemini_model(
                GEMINI_FALLBACK_MODEL,
                prompt
            )

            response_time = round(
                time.perf_counter() - start_time,
                2
            )

            return {
                "provider": "Gemini",
                "status": "available",
                "answer": fallback_answer,
                "model_used": GEMINI_FALLBACK_MODEL,
                "fallback_used": True,
                "fallback_reason_code": primary_error_code,
                "error_code": None,
                "error_message": None,
                "court_message": None,
                "attempts": 2,
                "response_time_seconds": response_time
            }

        except Exception as fallback_error:
            fallback_error_code = get_error_code(
                fallback_error
            )

            response_time = round(
                time.perf_counter() - start_time,
                2
            )

            combined_error = (
                f"Primary {GEMINI_MODEL} failed "
                f"({primary_error_code}): {primary_error}; "
                f"fallback {GEMINI_FALLBACK_MODEL} failed "
                f"({fallback_error_code}): {fallback_error}"
            )

            return {
                "provider": "Gemini",
                "status": "unavailable",
                "answer": None,
                "model_used": None,
                "fallback_used": False,
                "fallback_reason_code": primary_error_code,
                "error_code": fallback_error_code,
                "error_message": combined_error,
                "court_message": court_message(
                    fallback_error_code,
                    retrying=False
                ),
                "attempts": 2,
                "response_time_seconds": response_time
            }


# =========================================================
# GENERATE ALL THREE PROVIDER RESPONSES
# =========================================================

def generate_answers(prompt):

    openai_result = run_with_retries(
        "OpenAI",
        lambda: ask_openai(prompt)
    )

    claude_result = run_with_retries(
        "Claude",
        lambda: ask_claude(prompt)
    )

    gemini_result = run_gemini(
        prompt
    )

    provider_results = {
        "OpenAI": openai_result,
        "Claude": claude_result,
        "Gemini": gemini_result
    }


    # =====================================================
    # ONLY SUCCESSFUL TESTIMONY GOES TO THE JUDGE
    # =====================================================

    answers = {}

    for provider, result in provider_results.items():

        if (
            result["status"] == "available"
            and result["answer"]
        ):

            answers[provider] = result["answer"]


    return {
        "answers": answers,
        "provider_results": provider_results
    }