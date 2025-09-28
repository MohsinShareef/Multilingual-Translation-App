import streamlit as st
import pandas as pd
from googletrans import Translator, LANGUAGES
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Multilingual Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for better UI ---
st.markdown("""
<style>
    .stTextArea textarea {
        font-size: 1.1rem;
        border: 2px solid #2e3b4e;
        border-radius: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# --- Translator Initialization (Cached) ---
@st.cache_resource
def load_translator():
    """Load and cache the Translator instance."""
    return Translator()

translator = load_translator()

# --- Application State ---
# Initialize session state with lowercase names to match the library
if 'history' not in st.session_state:
    st.session_state.history = []
if 'source_lang' not in st.session_state:
    st.session_state.source_lang = "Automatic Detection"
if 'target_lang' not in st.session_state:
    # THIS IS THE CORRECTED LINE
    st.session_state.target_lang = "urdu"


# --- Helper Functions ---
def perform_translation(text, src, dest):
    """Translates a given text and handles errors."""
    if not text or not text.strip():
        return None, None
    try:
        # If source is 'auto', detect language first
        if src == 'auto':
            detected_lang = translator.detect(text).lang
            src = detected_lang
        
        translation = translator.translate(text, src=src, dest=dest)
        return translation.text, src
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None

def swap_languages():
    """Swaps the selected source and target languages safely."""
    source, target = st.session_state.source_lang, st.session_state.target_lang

    # The new source will be the old target. This is always a valid language.
    st.session_state.source_lang = target

    # The new target is the old source, but ONLY if it's not "Automatic Detection".
    if source != "Automatic Detection":
        st.session_state.target_lang = source


# --- Sidebar Navigation ---
with st.sidebar:
    st.title("Navigation")
    app_mode = st.radio(
        "Choose a mode",
        ["Interactive Translator", "Batch File Translator", "About"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.info(
        "This is a demonstration app using the unofficial googletrans library. "
        "For production use, a more robust, official API is recommended."
    )

# --- Main Application Logic ---
st.title("🌐 Multilingual Translation Application")

# ============================
# INTERACTIVE TRANSLATOR MODE
# ============================
if app_mode == "Interactive Translator":
    st.header("Translate Text Instantly")

    # Language dictionaries and options
    lang_values = list(LANGUAGES.values())
    lang_options = ["Automatic Detection"] + lang_values
    lang_codes = {name: code for code, name in LANGUAGES.items()}
    lang_codes["Automatic Detection"] = "auto"

    col1, swap_col, col2 = st.columns([5, 1, 5])
    with col1:
        st.selectbox(
            "From:",
            options=lang_options,
            key='source_lang' # Key directly manages the state
        )
    with swap_col:
        st.button("🔄", on_click=swap_languages, help="Swap languages", use_container_width=True)
    with col2:
        st.selectbox(
            "To:",
            options=lang_values, # Target cannot be 'Automatic Detection'
            key='target_lang' # Key directly manages the state
        )

    # Text input and output areas
    input_text = st.text_area("Enter text to translate:", height=150, key="input_text")

    if st.button("Translate", type="primary"):
        src_code = lang_codes[st.session_state.source_lang]
        dest_code = lang_codes[st.session_state.target_lang]

        with st.spinner("Translating..."):
            translated_text, detected_src_code = perform_translation(input_text, src_code, dest_code)

        if translated_text:
            # We use .title() here only for display purposes, not for logic
            detected_language_name = LANGUAGES.get(detected_src_code, "Unknown").title()
            
            st.success("Translation complete!")
            if src_code == 'auto':
                st.info(f"Detected Source Language: **{detected_language_name}**")

            st.subheader("Translated Text:")
            # Using st.code provides a handy copy button
            st.code(translated_text, language=None)
            
            st.session_state.history.append({
                'original': input_text,
                'translated': translated_text,
                'source': st.session_state.source_lang,
                'target': st.session_state.target_lang,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })

    # Display translation history
    if st.session_state.history:
        st.markdown("---")
        with st.expander("📜 View Translation History", expanded=False):
            # Reverse to show latest first
            history_df = pd.DataFrame(st.session_state.history).iloc[::-1]
            st.dataframe(history_df, use_container_width=True)
            if st.button("Clear History"):
                st.session_state.history = []
                st.rerun()

# ============================
# BATCH FILE TRANSLATOR MODE
# ============================
elif app_mode == "Batch File Translator":
    st.header("Translate a CSV File")
    
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("**Data Preview:**")
            st.dataframe(df.head())
            
            text_column = st.selectbox("Select the column to translate:", df.columns)
            target_lang_name = st.selectbox("Select the target language:", list(LANGUAGES.values()))
            dest_code = {name: code for code, name in LANGUAGES.items()}[target_lang_name]

            if st.button("Translate File", type="primary"):
                with st.spinner(f"Translating {len(df)} rows. This may take a while..."):
                    translations = []
                    progress_bar = st.progress(0, text="Translating...")
                    
                    for i, text in enumerate(df[text_column]):
                        translated, _ = perform_translation(str(text), 'auto', dest_code)
                        translations.append(translated or "Error")
                        progress_bar.progress((i + 1) / len(df), text=f"Translating row {i+1}/{len(df)}")
                
                df[f'translated_{dest_code}'] = translations
                st.success("Batch translation completed!")
                st.dataframe(df)

                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Translated Data as CSV",
                    data=csv,
                    file_name=f"translated_{uploaded_file.name}",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error processing file: {e}")

# ============================
# ABOUT PAGE
# ============================
else:
    
    st.header("About This Application")
    st.markdown("""
    This application provides a user-friendly interface for translating text between multiple languages.
    
    ### ✨ Features
    - **Interactive Mode**: Instantly translate text snippets with automatic source language detection.
    - **Batch Mode**: Upload a CSV file to translate an entire column of text efficiently.
    - **Translation History**: Keeps a record of your recent translations within the current session.
    
    ### 🛠️ Technologies Used
    - **Streamlit**: For creating the interactive web interface.
    - **`googletrans`**: A Python library to interface with the Google Translate API.
    - **Pandas**: For handling data in the batch translation feature.
    
    **Disclaimer:** This application uses an unofficial and free API (`googletrans`), which may be unstable. For critical or high-volume translations, it is highly recommended to use an official, paid translation API.
    """)