User Guide
**System Document**

1. Hardware Requirements To ensure the Kemaslah application runs smoothly, the following minimum hardware is required:
Processor (CPU): Intel Core i5 or AMD Ryzen 5 (Multi-core recommended for background threading).
Memory (RAM): Minimum 8 GB (16 GB recommended for optimal AI model batch processing).
Storage: Minimum 5 GB of free disk space (to accommodate the PyTorch libraries, the pre-trained ResNet50 model, and the compiled executable).
Internet Connection: Required for authenticating users via Supabase and downloading shared files via MongoDB Atlas.
2. Software Requirements
Operating System: Windows 10 or Windows 11 (64-bit).
Program Development Tools (For Source Code): Python 3.10+, Visual Studio Code (or equivalent IDE).
Databases (Cloud-Hosted): No local database software installation is required, as the application connects remotely to PostgreSQL (via Supabase) and MongoDB Atlas.

**Installation**

The Kemaslah application is distributed as a pre-compiled, standalone package. To make the installation process as simple as possible for end-users, the application is hosted securely on GitHub. New users do not need to install Python, run any command-line setups, or execute SQL statements, as the databases are cloud-hosted and the application is fully bundled.
Step-by-Step Installation Guide:
Open your web browser and navigate to the project's official GitHub repository page.
On the right side of the repository page, locate the "Releases" section and click on the latest release (e.g., Version 1.0).
Under the "Assets" dropdown of the release, click to download the provided compressed archive file (e.g., Kemaslah_App_v1.0.zip).
Once the download is complete, locate the .zip file in your Downloads folder. Right-click the file and select "Extract All..." to extract the contents into a local directory on your computer (for example, C:\Users\YourName\Documents\Kemaslah).
Ensure your computer is connected to the internet, as the application requires network access to communicate with the Supabase and MongoDB cloud clusters upon launch.

**Operation Document**

This section provides a step-by-step guide on how to run the application and use its major features.
How to Run the System:
Navigate to the folder where you extracted the downloaded .zip file.
Open the newly extracted Kemaslah folder.
Scroll through the folder, locate the Kemaslah.exe application file, and double-click it to launch the software. (Note: Depending on your Windows security settings, you may need to click "More info" and "Run anyway" on the Microsoft Defender SmartScreen the very first time you launch it).
Test User Login Information: To evaluate the system without registering a new account, use the following credentials:
Role: Standard User
Email: testuser@kemaslah.com
Password: TestPassword123!

1. Authentication Page 
Email & Password Fields: For users to input their registered credentials.
"Login" Button: Authenticates the user against the Supabase database.
"Sign in with Google" Button: Opens a secure web browser to authenticate the user via Google OAuth 2.0.
"Forgot Password" Link: Redirects to the OTP email verification flow for password recovery.

2. Home Dashboard
Sidebar Navigation (Left): Allows the user to switch between Home, Files, Smart Archive, and Statistics.
Stat Cards (Top): Displays a visual progress bar indicating the total storage capacity versus the currently used space on the local disk.
Recent Files Table: Double-clicking any folder or file in this table will immediately open it.

3. File Browser Page 
TopBar Breadcrumbs (e.g., Home > Documents > Work): Clickable buttons that allow the user to instantly navigate back to parent folders.
Search Bar (Top Right): Executes a "Deep Search" that scans both file names and text content (inside PDFs, DOCX, etc.) for the queried keyword.
"⚙ Smart Organise" Button (Action Bar): Triggers the CNN AI model to scan selected images/videos and automatically sort them into the correct category folders.
Context Menu (Right-Click in Table): Provides access to standard file operations such as New Folder, Copy, Paste, and Delete (moves to Recycle Bin).

4. Smart Archive Page
Month/Year Dropdowns: Forces the user to select a valid start and end date. The "Continue" button validates that the start date is chronologically before the end date.
"Select All" Checkbox: Toggles the selection of all found old files.
Review Tree: Displays files grouped by their location. Users can uncheck specific files they wish to keep.
"Accept" Button: Commences the ZIP compression process, triggering the floating LoadingOverlay while it packs the files.

5. Statistics Page
File Distribution Pie Charts: Hovering over a slice (e.g., "Image & Video files") makes the slice explode outward. The legend categorises the data visually.
AI Model Performance Table: Displays the Precision, Recall, and F1-Score of the Machine Learning model.
APPENDIX B: Developer Guide
This section is intended for subsequent developers or examiners who wish to modify, recompile, or understand the backend infrastructure of the Kemaslah project.

**Necessary Software, APIs, and Libraries**
1. Development Environment & Compilers
Python 3.10+: The core programming language used.
PyInstaller (pip install pyinstaller): Used to bundle the application and its dependencies into a standalone .exe file. The build instructions are mapped in the Kemaslah.spec file.
2. Core Application Libraries (from requirements.txt)
GUI Framework: PyQt6
Machine Learning (CNN): torch (PyTorch), torchvision, albumentations, opencv-python (for video keyframe extraction).
Data Analysis & Deep Search: scikit-learn, pandas, PyPDF2, python-docx, openpyxl.
Local Backend Server: Flask, Authlib (for handling OAuth redirects).
Database Connectors: psycopg2 (PostgreSQL), pymongo (MongoDB Atlas).
3. External APIs and Cloud Services
Supabase: Provides the PostgreSQL database for user authentication.
MongoDB Atlas: Provides the GridFS cloud storage for the file-sharing feature.
Google Cloud Console: Provides the OAuth 2.0 API for the "Sign in with Google" feature.

**Authentication Details and Security Configurations**

All sensitive connections and authentication mechanisms are handled securely. In the production environment, these variables are loaded via environment variables (os.getenv), but are documented here for development setup.
1. Supabase (PostgreSQL) Database Used for storing user credentials (users table) and tracking login states (login_requests table).
Host: db.urzssrfwuyhkebkwcbdx.supabase.co
Database Name: postgres
User: postgres
(Password provided securely to the examiner/supervisor)
Security Requirement: Connections MUST be made using sslmode="require". User passwords are encrypted using bcrypt prior to database insertion.
2. MongoDB Atlas (GridFS) Used exclusively for storing shared file binaries and tracking file expiration dates (shared_files collection).
Connection URI: mongodb+srv://limzhihao0513_db_user:[PASSWORD]@kemaslahcluster.815xmwv.mongodb.net/?appName=KemasLahCluster
Database: kemaslah_db
3. Local Flask Server Security The local server runs on http://127.0.0.1:5000 to handle security tokens independently of the UI.
Flask Secret Key: Used for session security. Variable: FLASK_SECRET_KEY
Google OAuth Client ID: 565755337222-4m20r04qohjrsgdd80masi8br9g6m2it.apps.googleusercontent.com
App Password (Email OTP): The SMTP server utilises a secure Google App Password (KEMASLAH_APP_PASSWORD) to send 6-digit OTPs from the system email (limzhihao0513@gmail.com).
