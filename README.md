Multi-agent AI evaluation, synthesis, and final-answer quality control.

Prompt Bench sends one prompt to multiple AI models, evaluates their responses against a structured rubric, selects the strongest contributions, synthesizes a final answer, and runs a final QA check before delivery.



What it does

Stage

Purpose

Generate

OpenAI, Claude, and Gemini answer the same prompt independently.

Judge

Responses are evaluated blindly so provider identity does not influence scoring.

Score

Each response is rated on Factual Accuracy, Completeness, Relevance, Tone, and Clarity.

Synthesize

The strongest contributions are combined into one final response.

Final QA

The synthesized answer is checked before delivery and can trigger revision when needed.

Log

Run-level results are saved for later analysis and model-performance comparisons.

Why I built it

My background in AI quality assurance made me interested in a simple question:

What happens if AI output is treated like something that should be tested, compared, and validated instead of automatically trusted?

Prompt Bench is my answer to that question. It applies structured QA thinking to multi-model AI workflows so strong outputs are preserved, weak outputs are challenged, and the final answer passes through one more quality gate before being shown.

Evaluation rubric

The QA Judge scores each response across five dimensions:

Factual Accuracy

Completeness

Relevance

Tone

Clarity

The judge evaluates responses anonymously, while provider identity is stored separately for later analytics.

Key features

Multi-model response generation

Blind response evaluation

Structured quality scoring

Rule-based tie handling

Multi-agent synthesis

Final QA validation

Automatic revision attempts

Provider retry and fallback handling

Analytics-ready run logging

Streamlit interface

Tech stack

Python

Streamlit

OpenAI API

Anthropic API

Google Gemini API

CSV-based analytics logging

Git / GitHub

Project structure

app.py               Streamlit interface and application flow
generators.py        Provider response generation
qa_engine.py         Blind evaluation and scoring
synthesis_engine.py  Final-answer synthesis
final_qa.py          Final validation and revision logic
run_logger.py        Run-level analytics logging
JUDGE_RUBRIC.md      Evaluation criteria and judge rules
requirements.txt     Python dependencies

Current status

Functional prototype. The core pipeline is working end to end, including generation, evaluation, synthesis, final QA, revision handling, provider-error handling, and analytics logging.

Current development is focused on:

expanding analytics and model-comparison reporting

strengthening testing and edge-case coverage

improving documentation

preparing the project for deployment

What this project demonstrates

AI output evaluation and quality assurance

Multi-agent workflow design

Human-in-the-loop thinking

Error handling and fallback logic

Structured logging and observability

Prompt and rubric design

Python application development

Translating QA experience into an AI product workflow

Run locally

Clone the repository.

Create a virtual environment.

Install dependencies:

pip install -r requirements.txt

Add your API credentials to a local .env file.

Start the Streamlit app:

streamlit run app.py

API credentials and private run logs are intentionally excluded from the public repository.

Built by Aaron Ray as an independent AI evaluation and quality-assurance project.
