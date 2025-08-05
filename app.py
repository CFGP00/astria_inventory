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
        required_columns = ["{Name}", "{Link}", "{IsFolder}", "Modified", "{FilenameWithExtension}", "Editor.DisplayName"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing expected columns in JSON: {missing_columns}")
            st.stop()

        # Rename columns for display
        df_filtered = df[required_columns].copy()
        df_filtered.columns = ["Name", "Link", "IsFolder", "Modified", "FilenameWithExtension", "LastEditedBy"]
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

        # Apply filters
        if name_filter:
            df_filtered = df_filtered[df_filtered["Name"].str.contains(name_filter, case=False, na=False)]

        if type_filter == "Files only":
            df_filtered = df_filtered[df_filtered["IsFolder"] == False]
        elif type_filter == "Folders only":
            df_filtered = df_filtered[df_filtered["IsFolder"] == True]

        if filetype_filter:
            df_filtered = df_filtered[df_filtered["FileType"].isin(filetype_filter)]

        # Display results using custom HTML table
        st.write("### 📄 Filtered Results")
        html_table = """
        <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px 12px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #f4f4f4;
        }
        </style>
        <table>
            <tr>
                <th>Name</th>
                <th>File Type</th>
                <th>Is Folder</th>
                <th>Modified</th>
                <th>Last Edited By</th>
                <th>Link</th>
            </tr>
        """

        for _, row in df_filtered.iterrows():
            html_table += f"""
            <tr>
                <td>{row['Name']}</td>
                <td>{row['FileType']}</td>
                <td>{'Yes' if row['IsFolder'] else 'No'}</td>
                <td>{row['Modified'].strftime('%Y-%m-%d %H:%M')}</td>
                <td>{row['LastEditedBy']}</td>
                <td><a href="{row['Link']}" target="_blank">Open</a></td>
            </tr>
            """

        html_table += "</table>"
        st.write(html_table, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Please upload a SharePoint JSON file to begin.")

