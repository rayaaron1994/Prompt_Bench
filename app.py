from pathlib import Path

import streamlit as st

from generators import generate_answers
from qa_engine import judge_answers
from synthesis_engine import synthesize_answer
from final_qa import validate_final_answer
from run_logger import log_run


# =========================================================
# BRAND / PAGE SETUP
# =========================================================

BASE_DIR = Path(__file__).parent

logo_candidates = [
    BASE_DIR / "promptbench_logo.png",
    BASE_DIR / "promptbench(3).png",
    BASE_DIR / "promptbench.png",
    BASE_DIR / "logo.png",
]

LOGO_PATH = next(
    (
        path
        for path in logo_candidates
        if path.exists()
    ),
    None
)

st.set_page_config(
    page_title="Prompt Bench",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# =========================================================
# CUSTOM STYLES
# =========================================================

st.markdown(
    """
    <style>
        :root {
            --pb-olive: #626746;
            --pb-olive-bright: #7B8158;
            --pb-olive-soft: #AEB58A;
            --pb-bg: #10130C;
            --pb-panel: #191E13;
            --pb-panel-soft: #202619;
            --pb-text: #F7F5EE;
            --pb-muted: #C6C8B9;
            --pb-dim: #8E927F;
            --pb-border: rgba(190, 198, 145, 0.24);
            --pb-border-strong: rgba(190, 198, 145, 0.38);
        }

        html {
            scroll-behavior: smooth;
        }

        .stApp {
            background:
                radial-gradient(
                    circle at 8% 0%,
                    rgba(98, 103, 70, 0.38),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 94% 14%,
                    rgba(119, 125, 85, 0.14),
                    transparent 30%
                ),
                linear-gradient(180deg, #15190F 0%, #0F120B 100%);
            color: var(--pb-text);
        }

        header[data-testid="stHeader"] {
            height: 0;
            background: transparent;
        }

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        #MainMenu,
        footer {
            display: none !important;
            visibility: hidden !important;
        }

        .block-container {
            max-width: 940px;
            padding-top: 2.35rem;
            padding-bottom: 4.5rem;
        }

        h1, h2, h3 {
            color: var(--pb-text);
            letter-spacing: -0.025em;
        }

        p, label, .stCaption {
            color: var(--pb-muted);
        }

        a {
            color: #D0D69D !important;
            text-underline-offset: 3px;
        }

        a:hover {
            color: #E4E8C2 !important;
        }

        .pb-hero {
            padding: 0.5rem 0 1.7rem 0;
        }

        .pb-eyebrow {
            color: #BAC18C;
            font-size: 0.73rem;
            font-weight: 850;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        .pb-title {
            color: var(--pb-text);
            font-size: clamp(2.8rem, 6vw, 4.2rem);
            line-height: 0.96;
            font-weight: 860;
            letter-spacing: -0.06em;
            margin: 0;
        }

        .pb-subtitle {
            color: #D2D3C8;
            font-size: 1.02rem;
            line-height: 1.62;
            max-width: 700px;
            margin-top: 0.95rem;
            margin-bottom: 0.85rem;
        }

        .pb-flow-row {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.42rem;
            margin-top: 0.25rem;
        }

        .pb-flow-row span {
            color: #C9CEA0;
            background: rgba(98, 103, 70, 0.18);
            border: 1px solid rgba(190, 198, 145, 0.16);
            border-radius: 999px;
            padding: 0.28rem 0.55rem;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.015em;
        }

        .pb-flow-row b {
            color: #777D61;
            font-weight: 650;
            font-size: 0.76rem;
        }

        .pb-case-label {
            color: #AEB58A;
            font-size: 0.70rem;
            font-weight: 850;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-top: 0.55rem;
            margin-bottom: 0.18rem;
        }

        .pb-section-title {
            color: var(--pb-text);
            font-size: 1.72rem;
            font-weight: 820;
            letter-spacing: -0.03em;
            margin-top: 0;
            margin-bottom: 0.72rem;
        }

        .pb-helper {
            color: #959A86;
            font-size: 0.86rem;
            margin-top: -0.35rem;
            margin-bottom: 0.9rem;
        }

        div[data-testid="stTextArea"] textarea {
            background: rgba(25, 30, 19, 0.96);
            color: var(--pb-text);
            border: 1px solid var(--pb-border);
            border-radius: 15px;
            padding: 16px 17px;
            line-height: 1.55;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.015);
        }

        div[data-testid="stTextArea"] textarea::placeholder {
            color: #777C6A;
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: #929A6E;
            box-shadow: 0 0 0 2px rgba(146, 154, 110, 0.12);
        }

        .stButton > button {
            min-height: 3.1rem;
            background: linear-gradient(135deg, #7A8056, #656B48);
            color: #FFFFFF;
            border: 1px solid rgba(226, 231, 194, 0.22);
            border-radius: 14px;
            padding: 0.8rem 1.15rem;
            font-weight: 800;
            letter-spacing: 0.01em;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
            transition: 0.15s ease;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #8A9161, #737A50);
            color: #FFFFFF;
            border-color: rgba(226, 231, 194, 0.34);
            transform: translateY(-1px);
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
        }

        .stButton > button:focus {
            color: #FFFFFF;
            border-color: #AEB58A;
            box-shadow: 0 0 0 2px rgba(174, 181, 138, 0.15);
        }

        div[data-testid="stStatusWidget"] {
            background: rgba(27, 32, 20, 0.92);
            border: 1px solid var(--pb-border);
            border-radius: 14px;
            overflow: hidden;
        }

        div[data-testid="stStatusWidget"] summary {
            color: #E6E6DD;
            font-weight: 650;
        }

        div[data-testid="stAlert"] {
            border-radius: 14px;
            border-color: var(--pb-border) !important;
        }

        div[data-testid="stExpander"] {
            background: rgba(25, 30, 19, 0.80);
            border: 1px solid var(--pb-border);
            border-radius: 14px;
            overflow: hidden;
        }

        div[data-testid="stExpander"] summary {
            color: #E1E2D7;
            font-weight: 650;
            background: rgba(28, 33, 21, 0.92) !important;
        }

        div[data-testid="stExpander"] details {
            background: transparent !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background:
                linear-gradient(
                    145deg,
                    rgba(98, 103, 70, 0.16),
                    rgba(18, 22, 14, 0.96)
                );
            border-color: var(--pb-border-strong) !important;
            border-radius: 17px;
            box-shadow: 0 16px 38px rgba(0, 0, 0, 0.13);
        }

        .pb-ruling-label {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            color: #BBC18D;
            font-size: 0.72rem;
            font-weight: 850;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.55rem;
        }

        .pb-ruling-label::before {
            content: "";
            width: 18px;
            height: 2px;
            border-radius: 999px;
            background: #8D9566;
        }

        .pb-privacy-note {
            color: #878C7A;
            font-size: 0.78rem;
            line-height: 1.45;
            margin-top: 0.9rem;
        }

        .pb-how-label {
            color: #AEB58A;
            font-size: 0.69rem;
            font-weight: 850;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            margin-bottom: 0.22rem;
        }

        .pb-how-copy {
            color: #C7C9BC;
            font-size: 0.91rem;
            line-height: 1.55;
        }

        hr {
            border-color: var(--pb-border);
            margin-top: 2.1rem !important;
            margin-bottom: 1.4rem !important;
        }

        @media (max-width: 720px) {
            .block-container {
                padding-top: 1.5rem;
                padding-left: 1.05rem;
                padding-right: 1.05rem;
            }

            .pb-title {
                font-size: 2.75rem;
            }

            .pb-subtitle {
                font-size: 0.95rem;
            }

            .pb-flow-row {
                gap: 0.32rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

if LOGO_PATH is not None:

    logo_col, title_col = st.columns(
        [0.85, 5.4],
        vertical_alignment="center"
    )

    with logo_col:
        st.image(
            str(LOGO_PATH),
            width=96
        )

    with title_col:
        st.markdown(
            '<div class="pb-hero">'
            '<div class="pb-eyebrow">Multi-agent AI evaluation</div>'
            '<div class="pb-title">Prompt Bench</div>'
            '<div class="pb-subtitle">'
            'One prompt enters the chamber. Multiple AI agents respond, '
            'the Judge evaluates the testimony, and Prompt Bench returns '
            'one final ruling.'
            '</div>'
            '<div class="pb-flow-row">'
            '<span>3 agents</span><b>→</b>'
            '<span>Blind Judge</span><b>→</b>'
            '<span>Synthesis</span><b>→</b>'
            '<span>Final QA</span>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

else:

    st.markdown(
        '<div class="pb-hero">'
        '<div class="pb-eyebrow">Multi-agent AI evaluation</div>'
        '<div class="pb-title">Prompt Bench</div>'
        '<div class="pb-subtitle">'
        'One prompt enters the chamber. Multiple AI agents respond, '
        'the Judge evaluates the testimony, and Prompt Bench returns '
        'one final ruling.'
        '</div>'
        '<div class="pb-flow-row">'
        '<span>3 agents</span><b>→</b>'
        '<span>Blind Judge</span><b>→</b>'
        '<span>Synthesis</span><b>→</b>'
        '<span>Final QA</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# INPUT
# =========================================================

st.markdown(
    '<div class="pb-case-label">The case</div>'
    '<div class="pb-section-title">Bring a prompt before the bench</div>'
    '<div class="pb-helper">'
    'Ask a factual question, compare options, add constraints, or test an edge case.'
    '</div>',
    unsafe_allow_html=True
)

prompt = st.text_area(
    "Prompt",
    placeholder=(
        "Ask a question, give instructions, compare options, "
        "or try to break the bench..."
    ),
    height=155,
    label_visibility="collapsed"
)


# =========================================================
# RUN
# =========================================================

if st.button(
    "Call the Bench",
    type="primary",
    use_container_width=True
):

    if not prompt.strip():

        st.warning(
            "The bench needs a prompt before proceedings can begin."
        )

    else:

        try:

            with st.status(
                "Proceedings are underway...",
                expanded=True
            ) as bench_status:


                # =========================================
                # AGENT RESPONSES
                # =========================================

                st.write(
                    "🗣️ Hearing testimony from the agents..."
                )


                generation = generate_answers(
                    prompt
                )


                available_answers = (
                    generation[
                        "answers"
                    ]
                )


                provider_results = (
                    generation[
                        "provider_results"
                    ]
                )


                reporting_count = len(
                    available_answers
                )


                # =========================================
                # PROVIDER FAILURES
                # =========================================

                unavailable_results = [

                    result

                    for result
                    in provider_results.values()

                    if result[
                        "status"
                    ] == "unavailable"
                ]


                for result in unavailable_results:

                    error_code = (
                        result.get(
                            "error_code"
                        )
                        or "Unknown"
                    )

                    st.warning(
                        "A witness failed to appear. "
                        f"Court code: {error_code} — "
                        "the bench will proceed with "
                        "the available testimony."
                    )


                # =========================================
                # REQUIRE AT LEAST TWO AGENTS
                # =========================================

                if reporting_count < 2:

                    bench_status.update(
                        label="Proceedings suspended.",
                        state="error",
                        expanded=True
                    )

                    st.error(
                        "The bench did not receive enough "
                        "testimony to perform a reliable comparison. "
                        "Please try again."
                    )

                    st.stop()


                # =========================================
                # JUDGE
                # =========================================

                st.write(
                    "⚖️ The Judge is reviewing the evidence..."
                )


                judge_result = judge_answers(
                    prompt,
                    available_answers
                )


                # =========================================
                # SYNTHESIS
                # =========================================

                st.write(
                    "📝 Preparing the final ruling..."
                )


                synthesis_result = (
                    synthesize_answer(
                        prompt,
                        judge_result
                    )
                )


                synthesized_answer = (
                    synthesis_result[
                        "final_answer"
                    ]
                )


                # =========================================
                # FINAL QA
                # =========================================

                st.write(
                    "🔎 Running final review..."
                )


                final_result = (
                    validate_final_answer(
                        prompt,
                        synthesized_answer,
                        judge_result
                    )
                )


                # =========================================
                # SAVE ANALYTICS
                # =========================================

                try:

                    log_run(
                        prompt,
                        generation,
                        judge_result,
                        synthesis_result,
                        final_result
                    )

                except Exception as logging_error:

                    print(
                        "Prompt Bench analytics logging failed:",
                        logging_error
                    )


                # =========================================
                # COMPLETE
                # =========================================

                if final_result[
                    "safe_to_show"
                ]:

                    bench_status.update(
                        label=(
                            "The bench has reached a ruling."
                        ),
                        state="complete",
                        expanded=False
                    )

                else:

                    bench_status.update(
                        label=(
                            "The ruling did not clear final review."
                        ),
                        state="error",
                        expanded=True
                    )


            # =================================================
            # FINAL ANSWER
            # =================================================

            if final_result[
                "safe_to_show"
            ]:

                st.divider()

                st.markdown(
                    '<div class="pb-ruling-label">Final ruling</div>',
                    unsafe_allow_html=True
                )

                with st.container(
                    border=True
                ):

                    st.markdown(
                        final_result[
                            "final_answer"
                        ]
                    )


                # =============================================
                # SOURCES USED IN FINAL ANSWER
                # =============================================

                used_source_ids = set(
                    final_result.get(
                        "used_source_ids",
                        []
                    )
                )


                source_catalog = {

                    int(source["id"]):
                        source

                    for source
                    in judge_result.get(
                        "evidence_packet",
                        {}
                    ).get(
                        "sources",
                        []
                    )

                    if source.get(
                        "id"
                    ) is not None
                }


                displayed_sources = [

                    source_catalog[
                        source_id
                    ]

                    for source_id
                    in sorted(
                        used_source_ids
                    )

                    if source_id
                    in source_catalog
                ]


                if displayed_sources:

                    with st.expander(
                        "Sources used"
                    ):

                        for source in displayed_sources:

                            source_id = (
                                source[
                                    "id"
                                ]
                            )

                            title = (
                                source[
                                    "title"
                                ]
                            )

                            url = (
                                source[
                                    "url"
                                ]
                            )

                            st.markdown(
                                f"**[{source_id}]** "
                                f"[{title}]({url})"
                            )


                st.markdown(
                    '<div class="pb-privacy-note">'
                    'Prompt Bench evaluates model outputs internally. '
                    'Provider identities and QA scoring stay behind the bench.'
                    '</div>',
                    unsafe_allow_html=True
                )


            else:

                st.error(
                    "The proposed response did not pass "
                    "Prompt Bench's final review. "
                    "Please try the request again."
                )


        # =====================================================
        # UNEXPECTED ERROR
        # =====================================================

        except Exception as error:

            st.error(
                "The bench encountered an unexpected issue."
            )

            with st.expander(
                "View technical details"
            ):

                st.code(
                    str(error)
                )


# =========================================================
# HOW IT WORKS
# =========================================================

st.write("")
st.divider()

with st.expander(
    "How Prompt Bench works"
):

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            '<div class="pb-how-label">1. Testimony</div>'
            '<div class="pb-how-copy">'
            'Three AI providers answer the same prompt independently.'
            '</div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            '<div class="pb-how-label">2. Evaluation</div>'
            '<div class="pb-how-copy">'
            'A blind Judge scores the responses and identifies reusable strengths.'
            '</div>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            '<div class="pb-how-label">3. Ruling</div>'
            '<div class="pb-how-copy">'
            'Synthesis builds one answer, then Final QA checks it before delivery.'
            '</div>',
            unsafe_allow_html=True
        )
