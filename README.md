Prompt Bench

A multi-agent AI evaluation system for comparing model responses, scoring quality, synthesizing stronger answers, and validating the final output before delivery.



Overview

Prompt Bench sends the same prompt to multiple AI providers, evaluates each response against a structured rubric, identifies the strongest contributions, synthesizes a final answer, and runs a final QA check before the result is shown.

The project grew out of my professional experience in AI quality assurance and my interest in building AI systems that are evaluated instead of automatically trusted.

Workflow

A user submits one prompt.

OpenAI, Claude, and Gemini generate independent responses.

A blind QA Judge evaluates the responses without seeing provider names.

Each response is scored on:

Factual Accuracy

Completeness

Relevance

Tone

Clarity

The strongest contributions are selected for synthesis.

A Synthesis Agent creates the final response.

Final QA validates the synthesized answer and can trigger a revision when needed.

Run-level results are logged for later analysis.

Key Features

Multi-model response generation

Blind response evaluation

Structured scoring rubric

Rule-based tie handling

Multi-agent synthesis

Final QA validation

Automatic revision attempts

Provider-error and retry handling

Analytics-ready run logging

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

generators.py — provider response generation

qa_engine.py — response evaluation and scoring

synthesis_engine.py — final-answer synthesis

final_qa.py — final validation and revision logic

run_logger.py — run-level analytics logging

JUDGE_RUBRIC.md — evaluation criteria and judge rules

Current Status

Functional prototype. The core pipeline is working end to end, including generation, evaluation, synthesis, final QA, revision handling, provider-error handling, and analytics logging.

Current development is focused on analytics, testing, documentation, and deployment.

Why I Built It

AI responses can sound confident while still containing factual errors, missing context, weak reasoning, or poor instruction-following. Prompt Bench explores a more deliberate approach: compare multiple outputs, evaluate them against explicit standards, preserve strong contributions, and validate the final answer before delivery.

What This Project Demonstrates

AI output evaluation and quality assurance

Multi-agent workflow design

Human-in-the-loop thinking

Error handling and fallback logic

Structured logging and observability

Practical use of multiple AI APIs

Iterative product development

Built by Aaron Ray as an independent AI evaluation and quality-assurance project.
