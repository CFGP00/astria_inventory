import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="SharePoint File Explorer", layout="wide")
st.title("📁 SharePoint File Explorer")

# File uploader
uploaded_file = st.file_uploader("Upload a SharePoint JSON file", type="json")

if uploaded_file is not None:
    try:
        raw_data = json.load(uploaded_file)
        if "value" not in raw_data:
            st.error("The uploaded JSON does not contain a 'value' key.")
            st.stop()

        data = raw_data["value"]
        df = pd.json_normalize(data)

        # Check required columns
        required_columns = ["{Name}", "{Link}", "{IsFolder}", "Modified", "{FilenameWithExtension}"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing expected columns in JSON: {missing_columns}")
            st.stop()

        # Rename columns for display
        df_filtered = df[required_columns].copy()
        df_filtered.columns = ["Name", "Link", "IsFolder", "Modified", "FilenameWithExtension"]
        df_filtered["Modified"] = pd.to_datetime(df_filtered["Modified"])

        # Classify file types
        def classify_file_type(filename):
            if not isinstance(filename, str):
                return "Other"
            ext = filename.lower().split('.')[-1]
            if ext in ['doc', 'docx']:
                return "Word"
            elif ext in ['ppt', 'pptx']:
                return "PowerPoint"
            elif ext in ['xls', 'xlsx']:
                return "Excel"
            elif ext == 'pdf':
                return "PDF"
            else:
                return "Other"

        df_filtered["FileType"] = df_filtered["FilenameWithExtension"].apply(classify_file_type)

        # Filters
        with st.sidebar:
            st.header("🔍 Filters")
            name_filter = st.text_input("Search by name")
            type_filter = st.selectbox("Show:", ["All", "Files only", "Folders only"])
            filetype_filter = st.multiselect("File type", options=sorted(df_filtered["FileType"].unique()))
            date_range = st.date_input("Modified date range", [])

        # Apply filters
        if name_filter:
            df_filtered = df_filtered[df_filtered["Name"].str.contains(name_filter, case=False, na=False)]

        if type_filter == "Files only":
            df_filtered = df_filtered[df_filtered["IsFolder"] == False]
        elif type_filter == "Folders only":
            df_filtered = df_filtered[df_filtered["IsFolder"] == True]

        if filetype_filter:
            df_filtered = df_filtered[df_filtered["FileType"].isin(filetype_filter)]

        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = pd.to_datetime(date_range)
            df_filtered = df_filtered[(df_filtered["Modified"] >= start_date) & (df_filtered["Modified"] <= end_date)]

        # Display results
        st.markdown(f"### 📄 {len(df_filtered)} items found")
        st.dataframe(df_filtered[["Name", "FileType", "IsFolder", "Modified", "Link"]].reset_index(drop=True))

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload a SharePoint JSON file to begin.")

