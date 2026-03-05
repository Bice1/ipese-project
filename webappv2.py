import streamlit as st
from pathlib import Path
import sys

# Add the Code directory to the path so we can import parser
sys.path.insert(0, str(Path(__file__).parent / "Code"))

from Code.parser import parse_iets_model

# Configure the page
st.set_page_config(
    page_title="IPESE Model Browser",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("📊 IPESE Model Browser")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select a view:",
        ["Overview", "Metadata", "Connectors", "Variables", "Calculations"]
    )

# Main content based on selected page
if page == "Overview":
    st.header("Overview")
    st.write("""
    Welcome to the IPESE Model Browser! This application allows you to explore the IETS Model.
    
    Use the sidebar to navigate between different views of the model data.
    """)
    
    # Load and display available sheets
    filepath = Path(__file__).parent / "Base" / "IETS_ModelName_v6.xlsx"
    data = parse_iets_model(str(filepath))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Metadata Rows", len(data.get('METADATA', [])))
    with col2:
        st.metric("Connectors Rows", len(data.get('CONNECTORS', [])))

elif page == "Metadata":
    st.header("Metadata")
    filepath = Path(__file__).parent / "Base" / "IETS_ModelName_v6.xlsx"
    data = parse_iets_model(str(filepath))
    
    if 'METADATA' in data:
        st.dataframe(data['METADATA'], use_container_width=True)
    else:
        st.warning("METADATA sheet not found")

elif page == "Connectors":
    st.header("Connectors")
    filepath = Path(__file__).parent / "Base" / "IETS_ModelName_v6.xlsx"
    data = parse_iets_model(str(filepath))
    
    if 'CONNECTORS' in data:
        st.dataframe(data['CONNECTORS'], use_container_width=True)
    else:
        st.warning("CONNECTORS sheet not found")

elif page == "Variables":
    st.header("Variables")
    st.info("Variables view coming soon...")

elif page == "Calculations":
    st.header("Calculations")
    st.info("Calculations view coming soon...")