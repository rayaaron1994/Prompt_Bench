Prompt Bench

Prompt Bench is a multi-agent AI evaluation system built to compare, judge, synthesize, and quality-check responses from multiple AI models.

Instead of relying on a single model response, Prompt Bench sends the same prompt to multiple AI providers, evaluates their answers against a structured rubric, selects the strongest contributions, synthesizes a final response, and performs a final QA check before delivery.

Why I Built This

AI responses can sound confident and useful while still containing factual errors, missing context, weak reasoning, or poor instruction-following.

My background in AI quality assurance made me interested in building a system that treats AI output as something that should be tested, compared, and validated — not automatically trusted.

Prompt Bench explores how multiple models, structured evaluation, and human-centered QA principles can work together to improve response quality.

How It Works

A user submits one prompt.

Multiple AI providers generate independent responses.

A QA Judge evaluates the responses anonymously.

Responses are scored across:

Factual Accuracy

Completeness

Relevance

Tone

Clarity

The strongest parts are selected for synthesis.

A Synthesis Agent creates the final response.

Final QA checks the synthesized response before delivery.

Run data is logged for later analysis.

Key Features

Multi-model response generation

Blind AI response evaluation

Structured quality scoring

Rule-based tie handling

Multi-agent synthesis

Final QA validation

Automatic revision attempts

Provider-error handling

Run logging for analytics

Streamlit interface

Tech Stack

Python

Streamlit

OpenAI API

Anthropic API

Google Gemini API

CSV-based analytics logging

Git / GitHub

Project Structure

app.py — Streamlit interface and application flow

generators.py — model/provider response generation

qa_engine.py — response evaluation and scoring

synthesis_engine.py — combines strongest response elements

final_qa.py — validates the synthesized final answer

run_logger.py — records run-level analytics

JUDGE_RUBRIC.md — evaluation criteria and judge rules

Current Status

Prompt Bench is a functional prototype.

The core multi-agent pipeline is working, including generation, evaluation, synthesis, final QA, revision handling, provider-error handling, and analytics logging.

Current development is focused on improving analytics, documentation, testing, and deployment.

What I Learned

Building Prompt Bench required thinking beyond simply calling an AI API. I had to design:

evaluation standards

tie-breaking logic

error handling

QA gates

fallback behavior

structured logging

provider independence

user-facing feedback

The project reinforced the importance of treating AI systems as workflows that require testing, observability, and quality controls rather than just prompt engineering.

About

Built by Aaron Ray as an independent AI evaluation and quality-assurance project.