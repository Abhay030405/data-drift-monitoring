import streamlit as st
import requests

st.title("Upload Dataset")

uploaded_file = st.file_uploader("Choose CSV, JSON, or Parquet file", type=["csv","json","parquet"])

if uploaded_file:
    st.write("Uploading...")
    response = requests.post(
        "http://127.0.0.1:8000/api/upload_data",
        files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
    )

    if response.status_code == 200:
        st.success("File uploaded successfully!")
        metadata = response.json()["metadata"]

        # Display basic info
        st.subheader("File Info")
        st.write(f"**Filename:** {metadata['filename']}")
        st.write(f"**Rows:** {metadata['rows']}")
        st.write(f"**Columns:** {metadata['columns']}")
        st.write("**Column Names:**")
        st.write(metadata["columns_names"])

        # Display missing values
        st.subheader("Missing Values")
        st.write("**Count per column:**")
        st.json(metadata["missing_values_count"])
        st.write("**Percentage per column (%):**")
        st.json(metadata["missing_percentage"])

        # Display duplicates
        st.subheader("Duplicate Rows")
        st.write(f"Total duplicate rows: {metadata['duplicate_rows']}")

    else:
        st.error(f"Upload failed: {response.text}")