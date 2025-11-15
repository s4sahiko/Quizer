# 🧠 QuizerAI: The Intelligent Quiz Generator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://quizerai.streamlit.app/)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue?style=flat-square)](https://www.python.org/downloads/)

A data-driven, interactive quiz application built with **Streamlit** and backed by **Firebase** for persistence and user management. This app is designed to create engaging and personalized quiz experiences.



## ✨ Features

 **Interactive Quizzes:** Engage users with multiple-choice questions.
  
 **Firebase Integration:** Utilizes Firebase Admin SDK for secure authentication, storing quiz data (Firestore), and potentially file storage (Storage).

 **Real-Time Feedback:** Provides immediate feedback on answers and tracks scores.
  
 **PDF/Document:** Capable of extracting questions or content from external documents (e.g., PDFs) for quiz generation.
  
 **One-Click Deployment:** Easily accessible and deployed via Streamlit Community Cloud.





## Try Now

You can try the live version of the application here:

👉 **[Launch QuizerAI App](https://quizerai.streamlit.app/)**



## 💻 Local Setup

If you want to run this application on your local machine, follow these steps:

### 1. Clone the Repository

    git clone [https://github.com/YOUR_GITHUB_USERNAME/quizer.git](https://github.com/s4sahiko/quizer.git)
    cd quizer

### 2. Create a Virtual Environment

       python -m venv venv
       source venv/bin/activate  # On Windows, use: venv\Scripts\activate
       
### 3. Install Dependencies

    pip install -r requirements.txt

### 4. Create a new folder ".streamlit/secrets.toml" and add
      GEMINI_API_KEY="........"

      firebase_creds = """
     {
       "type": "service_account",
       "project_id": "YOUR_PROJECT_ID",
       "private_key_id": "...",
       "private_key": "-----BEGIN PRIVATE KEY-----...",
       "client_email": "...",
       ...
     }
     """   
    
### 5. Run the App

    streamlit run quizer.py

## Contact:-

👤 Author: Sahiko
 
