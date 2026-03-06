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

# Load data once
filepath = Path(__file__).parent / "Base" / "IETS_ModelName_v6.xlsx"
data = parse_iets_model(str(filepath))

# Get available sheets for navigation
sheet_names = list(data.keys())

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select a view:",
        ["Overview"] + sheet_names
    )

# Main content based on selected page
if page == "Overview":
    st.header("Overview")
    st.write("""
    Welcome to the IPESE Model Browser! This application allows you to explore the IETS Model.
    
    Use the sidebar to navigate between different sheets of the model data.
    """)
    
    # Display metrics for all sheets
    st.subheader("Data Summary")
    cols = st.columns(len(data))
    
    for i, (sheet_name, df) in enumerate(data.items()):
        with cols[i]:
            st.metric(sheet_name, f"{len(df)} rows")

else:
    # Display selected sheet
    st.header(page)
    
    if page in data:
        df = data[page]
        
        # Display dataframe info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rows", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        
        # Display columns
        with st.expander("Column Names"):
            st.write(", ".join(df.columns.tolist()))
        
        # Display dataframe
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label=f"Download {page} as CSV",
            data=csv,
            file_name=f"{page}.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"Sheet '{page}' not found")