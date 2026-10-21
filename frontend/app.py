import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from rag import ask_randyll

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


def show_message(message):
    with st.chat_message(message["role"], avatar=AVATARS.get(message["role"])):
        st.markdown(message["content"])
        sources = message.get("sources") or []
        if sources:
            with st.expander("Retrieved sources", icon=":material/description:"):
                for source in sources:
                    st.caption(f"{source['filename']} — {source['page']}")


st.set_page_config(
    page_title="Randyll AI Assistant",
    page_icon=":material/school:",
    layout="centered",
)

st.title("Randyll Overseas AI Assistant", icon=":material/school:")
st.caption("Admissions, tuition, and scholarships for universities in South Korea")

with st.container(horizontal=True, gap="small"):
    st.badge("South Korea", icon=":material/public:", color="red")
    st.badge("University guides", icon=":material/menu_book:", color="blue")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    show_message(message)

question = st.chat_input(
    "Ask about Korean universities",
    submit_mode="disable",
)

if not st.session_state.messages:
    welcome = st.empty()
    with welcome.container():
        st.space("small")
        with st.container(border=True):
            st.markdown("Ask about a university, a degree level, or a document requirement.")
            st.caption("Answers come from the indexed university guides.")
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

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })
    show_message(st.session_state.messages[-1])

    sources = []
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.spinner("Searching university documents"):
            try:
                result = ask_randyll(question)
                answer = result["answer"]
                sources = result.get("sources") or []
                st.markdown(answer)
                if sources:
                    with st.expander("Retrieved sources", icon=":material/description:"):
                        for source in sources:
                            st.caption(f"{source['filename']} — {source['page']}")
            except Exception as error:
                answer = "An error occurred while processing your question."
                st.error(str(error), title=answer, icon=":material/error:")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
