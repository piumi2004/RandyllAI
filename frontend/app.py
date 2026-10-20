import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from rag import ask_randyll

st.set_page_config(
    page_title="Randyll AI Assistant",
    page_icon="🎓"
)

st.title("Randyll Overseas AI Assistant")
st.caption("South Korea University Information")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input(
    "Ask about Korean universities..."
)

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching university documents..."):
            try:
                result = ask_randyll(question)
                answer = result["answer"]

                st.markdown(answer)

                with st.expander("Retrieved sources"):
                    for source in result["sources"]:
                        st.write(
                            f"{source['filename']} "
                            f"— Page {source['page']}"
                        )

            except Exception as e:
                answer = "An error occurred while processing your question."
                st.error(f"{answer} {e}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })