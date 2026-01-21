import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="Data Analytics Chatbot",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stSidebar {
        background-color: #1A1A2E;
    }
    .stButton > button {
        background-color: #DC143C;
        color: white;
        border: none;
        border-radius: 5px;
    }
    .stButton > button:hover {
        background-color: #FF2D55;
    }
    h1, h2, h3 {
        color: #DC143C;
    }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None

with st.sidebar:
    st.title("📊 Data Analytics")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload your dataset", type=["csv", "xlsx"])
    
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.success(f"Loaded: {uploaded_file.name}")
        st.write(f"Rows: {len(st.session_state.df)}")
        st.write(f"Columns: {len(st.session_state.df.columns)}")

st.title("🤖 Data Analytics Chatbot")
st.markdown("*Powered by Claude AI*")

if st.session_state.df is not None:
    with st.expander("📋 Data Preview"):
        st.dataframe(st.session_state.df.head(10), use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", len(st.session_state.df))
    with col2:
        st.metric("Total Columns", len(st.session_state.df.columns))
    with col3:
        st.metric("Missing Values", st.session_state.df.isnull().sum().sum())

st.markdown("---")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about your data..."):
    if st.session_state.df is None:
        st.warning("Please upload a dataset first!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        df = st.session_state.df
        data_info = f"""
Columns: {list(df.columns)}
Shape: {df.shape}
Types: {df.dtypes.to_dict()}
Sample: {df.head(3).to_dict()}
"""
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        system_prompt = """You are a data analyst. When asked to visualize, provide Python code using plotly.
Use ```python code blocks. Keep responses brief."""

        with st.chat_message("assistant"):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Data:\n{data_info}\n\nQuestion: {prompt}"}
                ]
            )
            answer = response.content[0].text
            st.markdown(answer)
            
            if "```python" in answer:
                code = answer.split("```python")[1].split("```")[0]
                try:
                    exec_globals = {"pd": pd, "px": px, "go": go, "df": df, "st": st}
                    exec(code, exec_globals)
                    if "fig" in exec_globals:
                        st.plotly_chart(exec_globals["fig"], use_container_width=True)
                except Exception as e:
                    st.error(f"Chart error: {e}")
        
        st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    if st.session_state.df is None:
        st.info("👈 Upload a CSV or Excel file to get started!")