BookZone: AI-Powered Book Recommendation System
This is a personalized desktop application built using Python and Tkinter for the GUI, designed to help users find books based on their mood, reading history, and set personal goals.

✨ Features
Dashboard: Displays a catalog of books categorized by genre.

Reading Progress Tracking: Users can set books as 'Reading,' 'Read,' or 'Want to Read.'

Mood-Based Recommendation: Suggests books by analyzing user-inputted mood (slider) or detected facial expressions.

Voice Search: Allows users to search the book catalog using voice commands.


Shutterstock
Reading Goals: Tracks weekly/monthly progress against user-defined goals.

Amazon Integration: Provides a direct link to search for the book on Amazon (India).

🛠️ Technologies & Dependencies
This project requires the following major components to run:

Python 3.x

MySQL Server (for the database)

Required Python Libraries:

tkinter (Standard GUI library)

mysql.connector

Pillow (PIL) (for handling images)

SpeechRecognition

pyttsx3 (for text-to-speech feedback)

opencv-python (for camera-based mood detection)

numpy (required by other libraries)

🚀 Setup and Installation
Follow these steps to set up the environment and database locally.

1. Install Python Dependencies
Open your terminal or command prompt in the project directory and run:

Bash

pip install mysql-connector-python Pillow SpeechRecognition pyttsx3 opencv-python numpy
2. Database Setup (MySQL)
You must import the provided database file to create the tables and load the book data.

Start your MySQL Server.

Create the Database: Open your MySQL workbench or terminal and create the database named book_system:

SQL

CREATE DATABASE book_system;
Import the Data: Use the terminal (while inside your project folder) to load the data from the exported file:

Bash

mysql -u [YOUR_DB_USER] -p book_system < book_system_export.sql
(When prompted, enter your MySQL password.)

3. Update Configuration
You may need to update the database login credentials in the main Python file (open_main_app.py) to match your local MySQL username and password.

▶️ How to Run the Application
Once all setup steps are complete, run the main application file from your project directory:

Bash

python open_main_app.py
