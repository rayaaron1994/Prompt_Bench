import streamlit as st
import pandas as pd


# Temporary memory for completed evaluations
if "evaluations" not in st.session_state:
    st.session_state.evaluations = []


# App title
st.title("AI QA Evaluator")

st.write("Upload chatbot responses and evaluate their quality.")


# Upload CSV
uploaded_file = st.file_uploader(
    "Upload your chatbot responses",
    type="csv"
)


# Only run this section after a CSV is uploaded
if uploaded_file is not None:

    # Read the CSV
    data = pd.read_csv(uploaded_file)

    # Make row numbers start at 1
    data.index = data.index + 1

    # Show uploaded responses
    st.write(f"{len(data)} responses loaded")
    st.dataframe(data)


    # Choose a response
    st.subheader("Evaluate a response")

    selected_index = st.selectbox(
        "Choose a response",
        range(1, len(data) + 1)
    )

    selected_row = data.loc[selected_index]


    # Show selected response
    st.write("Prompt:")
    st.write(selected_row["prompt"])

    st.write("Bot response:")
    st.write(selected_row["bot_response"])

    st.write("Expected behavior:")
    st.write(selected_row["expected_behavior"])


    # Evaluation controls
    st.subheader("Score this response")

    accuracy = st.slider(
        "Accuracy",
        1,
        5,
        3
    )

    instruction_following = st.slider(
        "Instruction Following",
        1,
        5,
        3
    )

    completeness = st.slider(
        "Completeness",
        1,
        5,
        3
    )

    tone = st.slider(
        "Tone",
        1,
        5,
        3
    )

    result = st.selectbox(
        "Overall Result",
        ["Pass", "Needs Review", "Fail"]
    )

    notes = st.text_area(
        "Reviewer Notes"
    )


    # Submit evaluation
    if st.button("Submit Evaluation"):

        average_score = (
            accuracy
            + instruction_following
            + completeness
            + tone
        ) / 4

        evaluation = {
            "response_number": selected_index,
            "prompt": selected_row["prompt"],
            "accuracy": accuracy,
            "instruction_following": instruction_following,
            "completeness": completeness,
            "tone": tone,
            "average_score": average_score,
            "result": result,
            "notes": notes
        }

        st.session_state.evaluations.append(evaluation)

        st.success("Evaluation submitted!")

        st.write(f"Average Score: {average_score:.1f}/5")
        st.write(f"Overall Result: {result}")


    # Show all completed evaluations
    if st.session_state.evaluations:

        st.subheader("Completed Evaluations")

        evaluation_data = pd.DataFrame(
            st.session_state.evaluations
        )

        st.dataframe(
            evaluation_data,
            hide_index=True
        )