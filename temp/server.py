import streamlit as st
import pymongo
from zipfile import ZipFile
import os
import random
import time

# Initialize MongoDB client
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["file_sharing_db"]
collection = db["uploaded_files"]

# Function to create a zip file from uploaded files
def create_zip_file(uploaded_files, unique_code):
    temp_dir = "temp_upload"
    os.makedirs(temp_dir, exist_ok=True)

    if len(uploaded_files) == 1:
        # Store the single file as it is
        single_file = uploaded_files[0]
        filename = f"uploaded_file_{unique_code}_{single_file.name}"
        with open(os.path.join(temp_dir, filename), "wb") as f:
            f.write(single_file.read())
    else:
        for idx, file in enumerate(uploaded_files):
            filename = f"{file.name}"
            with open(os.path.join(temp_dir, filename), "wb") as f:
                f.write(file.read())

    zip_filename = f"uploaded_files_{unique_code}.zip"
    with ZipFile(zip_filename, "w") as zip:
        for file in os.listdir(temp_dir):
            zip.write(os.path.join(temp_dir, file), os.path.basename(file))

    return zip_filename

# Streamlit app
st.title("File Sharing App")

# Sidebar menu options
menu = st.sidebar.selectbox("Menu", ["Home", "Upload", "Download"])

if menu == "Upload":
    st.subheader("Upload Files")
    recipient_email = st.text_input("Recipient's Email")
    uploaded_files = st.file_uploader("Upload Files", type=["pdf", "txt", "png", "jpg"], accept_multiple_files=True)

    if uploaded_files:
        st.success("Files uploaded successfully!")

    unique_code = random.randint(100000, 999999)
    st.markdown("### Unique 6-Digit Code")
    st.info(f"The unique code for this upload is: {unique_code}")

    if st.button("Share Files as Zip"):
        if not recipient_email:
            st.error("Please enter the recipient's email.")
        elif not uploaded_files:
            st.error("Please upload files.")
        else:
            st.info("Creating a zip file...")

            # Simulate file upload progress (you can replace this with actual upload logic)
            progress_bar = st.progress(0)
            if len(uploaded_files) > 1:
                zip_filename = create_zip_file(uploaded_files, unique_code)
            else:
                zip_filename = None
            
            for percent_complete in range(101):
                time.sleep(0.1)  # Simulate upload time
                progress_bar.progress(percent_complete)

            # Upload the zip file and save it to MongoDB or your storage
            st.success(f"Files shared with {recipient_email}. Unique code: {unique_code}")

# Handle file download logic in the "Download" menu option (not shown in this snippet)
# You will need to create a new route to download files from MongoDB.
