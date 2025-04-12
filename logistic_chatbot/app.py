import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
from utils import (
    ask_gpt,
    ask_gpt_with_data,
    save_chat_history,
    clear_chat_history,
    validate_dataframe,
    get_chat_history,
    save_conversation_metadata,
    get_conversation_metadata
)

# ---- Constants ----
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = ["xlsx", "xls", "csv"]
MAX_DISPLAY_ROWS = 100

# ---- Setup page ----
st.set_page_config(
    page_title="Logistics Analyst",
    page_icon="📊",
    layout="centered",
    menu_items={
        'About': "### Logistics Data Analyst v3.0\nAI-powered data insights"
    }
)
st.title("📊 Logistics Data Analyst")

# ---- Initialize Session State ----
def initialize_session():
    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = get_chat_history(st.session_state.current_conversation + ".json")
    if "uploaded_df" not in st.session_state:
        st.session_state.uploaded_df = None
    if "file_name" not in st.session_state:
        st.session_state.file_name = None
    if "conversations" not in st.session_state:
        st.session_state.conversations = get_conversation_metadata()

initialize_session()

# ---- Sidebar ----
with st.sidebar:
    st.header("⚙️ Data Settings")
   
    # File Uploader
    st.subheader("📁 Upload Logistics Data")
    uploaded_file = st.file_uploader(
        "Upload your logistics data file",
        type=ALLOWED_FILE_TYPES,
        help=f"Supports Excel and CSV files up to {MAX_FILE_SIZE_MB}MB"
    )
   
    if uploaded_file:
        try:
            file_size = uploaded_file.size / (1024 * 1024)
            if file_size > MAX_FILE_SIZE_MB:
                st.error(f"File too large. Max size: {MAX_FILE_SIZE_MB}MB")
            else:
                with st.spinner("Analyzing data..."):
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                   
                    validate_dataframe(df)
                    st.session_state.uploaded_df = df
                    st.session_state.file_name = uploaded_file.name
                    st.success(f"✅ {uploaded_file.name} loaded successfully!")
                   
                    with st.expander("🔍 Data Preview"):
                        st.dataframe(df.head(min(len(df), MAX_DISPLAY_ROWS)))
                        st.caption(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
       
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
            st.session_state.uploaded_df = None

    # Delete uploaded data button
    if st.session_state.uploaded_df is not None:
        if st.button("🗑️ Delete Uploaded Data", use_container_width=True, key="delete_data"):
            st.session_state.uploaded_df = None
            st.session_state.file_name = None
            st.rerun()

    # Analysis Controls
    st.subheader("🔍 Analysis Options")
    analysis_depth = st.selectbox(
        "Analysis Depth",
        ["Quick Overview", "Detailed Analysis", "Deep Examination"],
        help="Choose how thoroughly to analyze the data"
    )
   
    # Chat Management
    st.subheader("💬 Conversation History")
    
    # Conversation list
    conversations = st.session_state.conversations
    if conversations:
        selected_conv = st.selectbox(
            "Saved Conversations",
            options=[conv["title"] for conv in conversations],
            format_func=lambda x: x[:50] + "..." if len(x) > 50 else x,
            key="conv_select"
        )
        
        if st.button("🔍 Load Conversation", use_container_width=True):
            selected_conv_data = next(conv for conv in conversations if conv["title"] == selected_conv)
            st.session_state.current_conversation = selected_conv_data["id"]
            st.session_state.messages = get_chat_history(selected_conv_data["id"] + ".json")
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear Current Chat", use_container_width=True):
            st.session_state.messages = []
            save_chat_history([], st.session_state.current_conversation + ".json")
            st.rerun()
    with col2:
        if st.button("🆕 New Conversation", use_container_width=True):
            new_conv_id = str(uuid.uuid4())
            new_conv_title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            st.session_state.conversations.append({
                "id": new_conv_id,
                "title": new_conv_title,
                "created_at": datetime.now().isoformat()
            })
            save_conversation_metadata(st.session_state.conversations)
            
            st.session_state.current_conversation = new_conv_id
            st.session_state.messages = []
            st.session_state.uploaded_df = None
            st.session_state.file_name = None
            st.rerun()

# ---- Display Chat History ----
for message in st.session_state.messages:
    avatar = "🛒" if message["role"] == "user" else "📊"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if "data_insights" in message:
            with st.expander("View Data Insights"):
                st.write(message["data_insights"])

# ---- Chat Input ----
if prompt := st.chat_input("Ask about the logistics data..."):
    # Display user message
    with st.chat_message("user", avatar="🛒"):
        st.markdown(prompt)
   
    # Generate and display assistant response
    with st.chat_message("assistant", avatar="📊"):
        with st.spinner("🔍 Analyzing data..."):
            try:
                if st.session_state.uploaded_df is not None:
                    response = ask_gpt_with_data(
                        prompt=prompt,
                        df=st.session_state.uploaded_df,
                        system_content=f"""
                        You are a Logistics Data Analyst. Provide {analysis_depth} of this data.
                        Include specific numbers and actionable insights when possible.
                        """
                    )
                else:
                    response = ask_gpt(
                        prompt=prompt,
                        system_content="You are a Logistics Expert. Provide helpful information."
                    )
               
                st.markdown(response)
               
                message = {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                }
               
                if st.session_state.uploaded_df is not None:
                    message["data_insights"] = {
                        "file": st.session_state.file_name,
                        "shape": st.session_state.uploaded_df.shape
                    }
               
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append(message)
                save_chat_history(st.session_state.messages, st.session_state.current_conversation + ".json")
               
                # Update conversation title if it's the first message
                if len(st.session_state.messages) == 2:
                    new_title = prompt[:50] + "..." if len(prompt) > 50 else prompt
                    for conv in st.session_state.conversations:
                        if conv["id"] == st.session_state.current_conversation:
                            conv["title"] = new_title
                    save_conversation_metadata(st.session_state.conversations)
               
            except Exception as e:
                st.error(f"⚠️ Analysis failed: {str(e)}")

# ---- Data Summary Section ----
if st.session_state.uploaded_df is not None:
    with st.expander("📈 Data Summary", expanded=False):
        tab1, tab2 = st.tabs(["Statistics", "Sample Data"])
       
        with tab1:
            st.subheader("Statistical Summary")
            st.write(st.session_state.uploaded_df.describe())
       
        with tab2:
            st.subheader("Data Sample")
            st.dataframe(st.session_state.uploaded_df.sample(min(10, len(st.session_state.uploaded_df))))