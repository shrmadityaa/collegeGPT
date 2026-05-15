import streamlit as st
from pathlib import Path

from src.rag_chat import CollegeGPT
from src.extractor.text_extraction import run_extraction


st.set_page_config(
    page_title="CollegeGPT",
    layout="wide"
)

st.title("🎓 CollegeGPT")

st.markdown(
    "Upload a syllabus PDF and ask questions from it."
)

# Upload PDF
uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)

if uploaded_file:

    pdf_path = Path(
        "data/raw_pdfs/uploaded.pdf"
    )

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success("PDF uploaded successfully.")

    # Run extraction
    output_path = (
        "data/extracted_text/uploaded.txt"
    )

    run_extraction(
        str(pdf_path),
        output_path
    )

    st.success(
        "Text extracted successfully."
    )

    st.info(
        "Embedding regeneration currently "
        "needs manual execution."
    )

# Load chatbot
@st.cache_resource
def load_chatbot():
    return CollegeGPT()

chatbot = load_chatbot()

query = st.text_input(
    "Ask a question"
)

if st.button("Ask"):

    if query.strip():

        with st.spinner("Thinking..."):

            result = chatbot.ask(query)

        st.subheader("Answer")

        st.write(result["answer"])

        st.subheader("Retrieved Sources")

        for i, source in enumerate(
            result["sources"],
            start=1
        ):

            with st.expander(
                f"Source {i} - {source.get('course')}"
            ):

                st.write(
                    source.get("text")
                )