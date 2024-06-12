# 3D Model Hub: Upload, View, and Download

## Overview
The 3D Model Hub is a web-based application designed to facilitate the uploading, viewing, and downloading of 3D models along with their associated textures. This application, built with Flask for the backend server, Dash for the frontend interface, and SQLite for database management, provides a user-friendly platform for managing 3D models and textures.

## Features

File Upload: Allows users to upload 3D model files and texture files via the web interface.
Database Management: Stores uploaded files in an SQLite database.
Model Rendering: Enables users to select and render uploaded models and textures for viewing.
Download Functionality: Provides the option to download rendered models with textures as ZIP files.
User-Friendly Interface: Features an intuitive web interface created with Dash.
Installation and Setup
Prerequisites
Python 3.x
Required Python libraries: Flask, Dash, Dash-Uploader


## Steps

1. Clone the Repository:

git clone https://github.com/ohsidno/3D_Model_Viewer_and_Converter.git

cd 3d-model-hub


2. Install Required Libraries:

pip install -r requirements.txt

IMPORTANT - Set Python home directory (.venv/pyvenv.cfg)

3. Run the Application:

python app.py
Access the Web Interface:
Open a web browser and navigate to http://localhost:8050/dash/.


## Report


### Components

Flask Application: Manages server-side operations, including routing and file serving.

Dash Application: Provides the web interface for user interactions using Dash for interactive web components.

SQLite Database: Stores information about uploaded files and their content.

Logging: Logs activities and errors for debugging and monitoring purposes.


## Directory Structure

uploads/: Stores uploaded 3D model files.

temp_uploads/: Stores temporary files.

texture_uploads/: Stores uploaded texture files.

downloads/: Stores downloadable ZIP files.


## Dependencies
Standard Libraries: os, logging, zipfile, sqlite3, base64, threading, time, webbrowser
Dash and Flask Libraries: dash, dash_core_components (dcc), dash_html_components (html), dash.dependencies, Flask, redirect, send_file
File Upload Utilities: dash_uploader, werkzeug.utils.secure_filename


## File Conversion Process
The application converts uploaded files into a format suitable for viewing and downloading by processing and storing them in the SQLite database. The files are stored in binary format, and the conversion is handled as part of the file upload and rendering process.

Uploading Source Files: The source file is uploaded, saved temporarily, and stored in the database.
Uploading Texture Files: The texture file is uploaded, saved temporarily, and stored in the database.
Rendering: The selected source and texture files are processed and rendered for viewing.
Downloading: The rendered model and texture files are compressed into a ZIP file for download.


# User Manual

## Uploading Files

1. Upload a 3D Model:

Locate the "Upload Source File" section.
Click on the area that says "Drag and Drop or Select a 3D model file".
A file dialog will appear. Navigate to and select the 3D model file you want to upload.
The selected file will begin uploading. Once the upload is complete, a confirmation message will appear below the upload area.


2. Upload a Texture File:

Locate the "Upload Texture File" section.
Click on the area that says "Drag and Drop or Select a texture file".
A file dialog will appear. Navigate to and select the texture file you want to upload.
The selected file will begin uploading. Once the upload is complete, a confirmation message will appear below the upload area.


3. Refreshing the Texture List

After uploading a texture file, click the "Refresh Texture List" button to update the texture file dropdown menu with the newly uploaded texture.
Selecting and Rendering Models

4. Select a 3D Model File:

Locate the "Source File" dropdown menu.
Click on the dropdown menu to see a list of uploaded 3D model files.
Select the 3D model file you want to render.
Select a Texture File:

Locate the "Texture File" dropdown menu.
Click on the dropdown menu to see a list of uploaded texture files.
Select the texture file you want to apply to the 3D model.


5. Render the Model:

The rendered model will be displayed in the viewer area. Use your mouse to interact with the model:

Rotate: Click and drag the model to rotate it.
Zoom: Use the mouse scroll wheel to zoom in and out.
Pan: Hold down the middle mouse button (or both left and right buttons) and drag to pan the view.

6. Downloading the Rendered Model:

After rendering, a download link will appear .
Click the link to download the ZIP file containing the rendered 3D model and texture.
Save the ZIP file to your desired location on your computer.

## Troubleshooting Tips

File Upload Issues:

Ensure the file size does not exceed 50 MB.
Confirm that the file format is supported (commonly used formats include .obj for 3D models and .jpg/.png for textures).

Rendering Issues:

Check the browser console for any error messages.
Ensure the selected files are correctly uploaded.

Download Issues:

Verify that the downloads directory is writable.
Check the application logs (app.log) for any errors during the zipping process.

By following these instructions, you can effectively use the 3D Model Hub UI to manage your 3D models and textures. Enjoy exploring and creating with your 3D models!

## References

Flask: Flask Documentation (https://pypi.org/project/Flask/)

Dash: Dash Documentation (https://pypi.org/project/dash/)

SQLite: SQLite Documentation (https://docs.python.org/3/library/sqlite3.html)

Dash Uploader: Dash Uploader Documentation (https://pypi.org/project/dash-uploader/)

Werkzeug: Werkzeug Documentation (https://pypi.org/project/Werkzeug/)
