import streamlit as st
import pymongo
from bson import Binary
import random
import zipfile
from io import BytesIO
import time
import os
import base64
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from tempfile import NamedTemporaryFile
from datetime import datetime, date, timedelta
from decouple import config





def download_file(unique_code):
    file_info = collection.find_one({"unique_code": int(unique_code)})

    if file_info:
        recipient_email = file_info["recipient_email"]
        file_data = file_info["file_data"]
        file_name = file_info["file_name"]

        st.info(f"Downloading file for {recipient_email} with unique code {unique_code}")

        # Create a temporary file to store the downloaded data
        temp_file = NamedTemporaryFile(delete=False, suffix=file_name)

        with open(temp_file.name, "wb") as f:
            f.write(file_data)

        st.success("File downloaded successfully!")

        # Provide a link for the user to download the file
        st.markdown(f"**[Download {file_name}]({temp_file.name})**")

    else:
        st.error("File not found. Please check the unique code.")


# Initialize MongoDB client
#client = pymongo.MongoClient("mongodb://localhost:27017/")
#db = client["file_sharing_db"]
#collection = db["uploaded_files"]

# Replace with your MongoDB Atlas connection string
connection_string = config('MONGODB_URI')
# Create a MongoDB client using the connection string
client = pymongo.MongoClient(connection_string)

# Access your specific MongoDB database
db = client["filedump"]  # Replace "your-database-name" with your actual database name
collection = db["uploaded_files"]

# Mailgun API configuration
MAILGUN_API_KEY = config('MAILGUN_API_KEY')
MAILGUN_DOMAIN = config('MAILGUN_DOMAIN')

# Now you can use these variables in your application
print(f'MongoDB URI: {connection_string}')
print(f'Mailgun API Key: {MAILGUN_API_KEY}')
print(f'Mailgun Domain: {MAILGUN_DOMAIN}')

# Function to send an email
def send_email(recipient_email, unique_id):
    web_app_url = "https://your-web-app-url.com"  # Replace with the actual URL
    subject = "File has been uploaded for you on Fileshare"
    message = f"Hello!\n\nA file has been uploaded for you on Fileshare. Below is the unique ID to access your file:\n\n{unique_id}\n\nYou can access the web app here: {web_app_url}"
    
    data = {
        "from": "your_email@your_domain.com",  # Replace with your sender email
        "to": recipient_email,
        "subject": subject,
        "text": message
    }

    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data=data
    )

    if response.status_code == 200:
        return True  # Email sent successfully
    else:
        return False  # Failed to send email

# Function to periodically delete files older than two months
def delete_old_files():
    two_months_ago = datetime.now() - timedelta(days=60)
    result = collection.delete_many({"upload_date": {"$lt": two_months_ago}})
    st.write(f"Deleted {result.deleted_count} files older than two months.")

# Schedule the cleanup function to run periodically (e.g., daily)
scheduler = BackgroundScheduler()
scheduler.add_job(delete_old_files, 'interval', days=1)  # Adjust the schedule as needed
scheduler.start()



# Function to upload the file to MongoDB with the actual file name
def upload_file(recipient_email, uploaded_file):
    unique_code = random.randint(100000, 999999)
    # Extract file extension
    file_extension = os.path.splitext(uploaded_file.name)[-1]
    # Read file data
    file_data = uploaded_file.read()
    
    # Store the original file name, extension, and data in MongoDB
    file_id = collection.insert_one({
        "recipient_email": recipient_email,
        "file_data": Binary(file_data),
        "unique_code": unique_code,
        "file_name": uploaded_file.name,  # Store the original file name
        "file_extension": file_extension
    })
    send_email(recipient_email, unique_code)
    return unique_code

# Function to upload multiple files as a ZIP file to MongoDB
def upload_files_as_zip(recipient_email, uploaded_files):
    unique_code = random.randint(100000, 999999)
    # Create a BytesIO stream to hold the ZIP file
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, "w", zipfile.ZIP_DEFLATED) as zipf:
        for uploaded_file in uploaded_files:
            # Extract file extension
            file_extension = os.path.splitext(uploaded_file.name)[-1]
            # Read file data
            file_data = uploaded_file.read()
            # Add file to the ZIP archive
            zipf.writestr(uploaded_file.name, file_data)
    
    # Store the ZIP file in MongoDB
    zip_data.seek(0)
    file_id = collection.insert_one({
        "recipient_email": recipient_email,
        "file_data": Binary(zip_data.read()),
        "unique_code": unique_code,
        "file_name": "uploaded_files.zip",  # You can change the ZIP file name as needed
        "file_extension": ".zip"
    })
    send_email(recipient_email, unique_code)
    return unique_code

#streamlitapp
# Function to get the total number of files in the database
def get_total_files_count():
    return collection.count_documents({})

# Function to get the total number of files deleted
def get_total_files_deleted():
    today = datetime.combine(date.today(), datetime.min.time())  # Convert date to datetime
    two_months_ago = today - timedelta(days=60)  # Calculate the date two months ago
    return collection.count_documents({"upload_date": {"$lt": two_months_ago}})

# Function to get the current number of files held in the database
def get_current_files_count():
    return get_total_files_count()

# Set the title using st.title
# Set the title and slogan with emojis and center them
st.markdown('<h1 style="text-align:center;">FileDump</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size:20px; text-align:center;">Share 📤 in a Snap, Download 📥 with a Bump! 🚀</p>', unsafe_allow_html=True)

# Create columns for the small panels
col1, col2, col3 = st.columns(3)

# Function to update the displayed information
def update_information():
    total_files = get_total_files_count()
    files_shared_today = get_total_files_deleted()
    current_files = get_current_files_count()

    # Update the displayed information
    with col1:
        st.info(f"Total Shared Files\n{total_files}")

    with col2:
        st.info(f"Total Files Deleted\n{files_shared_today}")

    with col3:
        st.info(f"Files Currently Held\n{current_files}")

# Initial update of the information
update_information()
# Features section
st.subheader("Features")

# Use emojis and Markdown for a vibrant look
st.markdown(" ✅ **Upload and share files**")
st.markdown(" 📦 **Share multiple files as a ZIP archive**")
st.markdown(" 🗑️ **Automatically delete files older than two months**")
st.markdown(" 📥 **Download files using a 6-Digit Unique Code**")
st.markdown(" 📧 **Email integration for alerting users when a file has been uploaded**")





# Sidebar menu options
# Sidebar menu
menu = st.sidebar.selectbox("Menu", ["Home", "Upload", "MultipleFiles", "Download"])

if menu == "MultipleFiles":
    st.subheader("Upload and send as Zip")
    # Input field for recipient's email
    recipient_email = st.text_input("Recipient's Email")

    # File uploader for multiple files
    uploaded_files = st.file_uploader("Upload Multiple Files", type=["pdf", "txt", "jpg", "png", "zip"], accept_multiple_files=True)

    if uploaded_files:
        st.success("Files uploaded successfully!")

    if st.button("Share Files as ZIP"):
        if not recipient_email:
            st.error("Please enter the recipient's email.")
        elif not uploaded_files:
            st.error("Please upload one or more files.")
        else:
            st.info("Processing wait a minute....")

            # Simulate file upload progress (you can replace this with actual upload logic)
            progress_bar = st.progress(0)

            unique_code = upload_files_as_zip(recipient_email, uploaded_files)

            for percent_complete in range(101):
                time.sleep(0.1)  # Simulate upload time
                progress_bar.progress(percent_complete)
            st.info("#### Unique 6-Digit Code")
            st.success(f"The unique code for this upload is: {unique_code}")
            
if menu == "Upload":
    st.subheader("Upload Files")
    recipient_email = st.text_input("Recipient's Email")
    uploaded_file = st.file_uploader("Upload a File")

    if uploaded_file:
        st.success("File uploaded successfully!")


    if st.button("Share File"):
        if not recipient_email:
            st.error("Please enter the recipient's email.")
        elif not uploaded_file:
            st.error("Please upload a file.")
        else:
            st.info("Processing wait a minute...")

            # Simulate file upload progress (you can replace this with actual upload logic)
            progress_bar = st.progress(0)

            unique_code = upload_file(recipient_email, uploaded_file)

            for percent_complete in range(101):
                time.sleep(0.1)  # Simulate upload time
                progress_bar.progress(percent_complete)

            st.info("#### Unique 6-Digit Code")
            st.success(f"The unique code for this upload is: {unique_code}")

if menu == "Download":
    def download_file(unique_code):
        file_info = collection.find_one({"unique_code": int(unique_code)})
        if file_info:
            recipient_email = file_info["recipient_email"]
            file_data = file_info["file_data"]
            file_name = file_info["file_name"]

            st.info(f"Downloading file for {recipient_email} with unique code {unique_code}")

            # Create a temporary file to store the downloaded data
            temp_file = BytesIO(file_data)
            temp_file.name = file_name

            # Provide a download button for the user
            st.download_button(
                label=f"Download {file_name}",
                data=temp_file,
                key=unique_code,
                file_name=file_name,  # Specify the desired filename
            )

        else:
            st.error("File not found. Please check the unique code.")

    st.title("File Download App")

    # Input field for the unique code
    unique_code = st.text_input("Enter the 6-Digit Unique Code")

    if st.button("Download File"):
        if len(unique_code) == 6 and unique_code.isdigit():
            download_file(unique_code)
        else:
            st.error("Invalid code. Please enter a 6-digit numeric code.")


st.markdown("<p style='font-size: small; text-align: center;'>Made with ❤️ by khushalsarode</p>", unsafe_allow_html=True)
