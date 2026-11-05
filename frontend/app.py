
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.rag import ask_randyll

AVATARS = {
    "user": ":material/person:",
    "assistant": ":material/school:",
}

SUGGESTIONS = {
    ":red[:material/account_balance:] Jeonbuk proof of funds": (
        "What is Jeonbuk's graduate proof-of-funds requirement?"
    ),
    ":blue[:material/payments:] Dongseo tuition": (
        "What is the tuition fee at Dongseo University?"
    ),
    ":red[:material/school:] Kyungpook admissions": (
        "What are the admission requirements at Kyungpook National University?"
    ),
    ":blue[:material/redeem:] Tongmyong scholarships": (
        "What scholarships does Tongmyong University offer?"
    ),
}


# ==========================================================
# DISPLAY CHAT MESSAGES
# ==========================================================

def show_message(message):
    with st.chat_message(
        message["role"],
        avatar=AVATARS.get(message["role"])
    ):
        st.markdown(message["content"])


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Randyll AI Assistant",
    page_icon=":material/school:",
    layout="centered",
)

st.title(
    "Randyll Overseas AI Assistant",
    icon=":material/school:"
)

st.caption(
    "Admissions, tuition, and scholarships for universities in South Korea"
)

with st.container(horizontal=True, gap="small"):
    st.badge(
        "South Korea",
        icon=":material/public:",
        color="red"
    )

    st.badge(
        "University guides",
        icon=":material/menu_book:",
        color="blue"
    )


# ==========================================================
# CHAT HISTORY
# ==========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    show_message(message)


# ==========================================================
# CHAT INPUT
# ==========================================================

question = st.chat_input(
    "Ask about Korean universities",
    submit_mode="disable",
)


# ==========================================================
# WELCOME SCREEN AND SUGGESTIONS
# ==========================================================

if not st.session_state.messages:
    welcome = st.empty()

    with welcome.container():
        st.space("small")

        with st.container(border=True):
            st.markdown(
                "Ask about a university, a degree level, "
                "or a document requirement."
            )

            st.caption(
                "Answers come from the indexed university guides."
            )

        selected = st.pills(
            "Try asking",
            list(SUGGESTIONS.keys()),
            label_visibility="collapsed",
            wrap=True,
        )

    if selected:
        question = SUGGESTIONS[selected]

    if question:
        welcome.empty()


# ==========================================================
# PROCESS USER QUESTION
# ==========================================================

if question:

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })

    # Display user message
    show_message(st.session_state.messages[-1])

    # Generate assistant answer
    with st.chat_message(
        "assistant",
        avatar=AVATARS["assistant"]
    ):

        with st.spinner("Thinking..."):

            try:
                result = ask_randyll(question)

                answer = result["answer"]

                # Display the answer only.
                # Retrieved sources are intentionally hidden.
                st.markdown(answer)

            except Exception as error:
                answer = (
                    "An error occurred while processing "
                    "your question."
                )

                st.error(
                    str(error),
                    title=answer,
                    icon=":material/error:"
                )

    # Save assistant response to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
    })
