import logging
import os
import sqlite3
from flask import Flask, send_file, redirect
from werkzeug.utils import secure_filename
import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import base64
import pyvista as pv
import sys
import zipfile
from io import BytesIO
import threading
import webbrowser
import time
import shutil
import os

def find_directory(start_dir, target_directory_name):
    for root, dirs, files in os.walk(start_dir):
        if target_directory_name in dirs:
            return os.path.join(root, target_directory_name)
    return None

# Specify the name of the DLL file to find
dll_filename = 'assimp-vc140-mt.dll'

# Specify the current directory
current_directory = os.getcwd()

# Specify the starting directory to search for the destination directory
start_directory = r'C:\\'  # Adjust this path to narrow down the search if needed

# Specify the name of the destination directory to find
destination_directory_name = 'impasse'

# Construct the full path to the DLL file in the current directory
source_path = os.path.join(current_directory, dll_filename)

if os.path.exists(source_path):
    # Find the destination directory
    destination_directory = find_directory(start_directory, destination_directory_name)
    
    if destination_directory:
        # Create the full destination path
        destination_path = os.path.join(destination_directory, dll_filename)

        # Copy the DLL file to the destination directory
        shutil.copy(source_path, destination_path)

        print(f'{source_path} has been copied to {destination_path}')
    else:
        print(f'Destination directory {destination_directory_name} not found.')
else:
    print(f'File {dll_filename} not found in the current directory {current_directory}')



import impasse as assimp


# Directories
DOWNLOAD_DIRECTORY = os.path.join(os.getcwd(), "downloads")
TEMP_UPLOAD_FOLDER = os.path.join(os.getcwd(), "temp_uploads")
TEXTURE_UPLOAD_FOLDER = os.path.join(os.getcwd(), "texture_uploads")

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)
if not os.path.exists(TEMP_UPLOAD_FOLDER):
    os.makedirs(TEMP_UPLOAD_FOLDER)
if not os.path.exists(TEXTURE_UPLOAD_FOLDER):
    os.makedirs(TEXTURE_UPLOAD_FOLDER)

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])

# Initialize Flask server
server = Flask(__name__)
DATABASE = 'files.db'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
server.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                filename TEXT UNIQUE,
                original_format TEXT,
                original_content BLOB,
                obj_content BLOB
            )''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS textures (
                id INTEGER PRIMARY KEY,
                obj_filename TEXT,
                texture_filename TEXT,
                texture_content BLOB,
                FOREIGN KEY (obj_filename) REFERENCES files (filename)
            )''')
        conn.commit()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@server.route('/')
def index():
    return redirect('/dash/')

@server.route('/texture_uploads/<filename>')
def serve_texture_file(filename):
    return send_file(os.path.join(TEXTURE_UPLOAD_FOLDER, filename))

@server.route('/download-model/<obj_filename>/<texture_filename>')
def download_model(obj_filename, texture_filename):
    obj_path = os.path.join(TEMP_UPLOAD_FOLDER, obj_filename)
    zip_filename = f"{os.path.splitext(obj_filename)[0]}_model.zip"
    zip_path = os.path.join(DOWNLOAD_DIRECTORY, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        zip_file.write(obj_path, arcname=obj_filename)
        if texture_filename != 'view_only_mesh':
            texture_path = os.path.join(TEXTURE_UPLOAD_FOLDER, texture_filename)
            zip_file.write(texture_path, arcname=texture_filename)
    
    return send_file(zip_path, as_attachment=True)

def convert_to_obj(input_path, output_path):
    try:
        logging.debug(f"Loading file for conversion: {input_path}")
        scene = assimp.load(input_path)
        if scene.meshes:
            logging.debug(f"Scene loaded successfully with {len(scene.meshes)} meshes")
            logging.debug(f"Exporting scene to OBJ: {output_path}")
            assimp.export(scene, output_path, file_type='obj')
            logging.debug(f"Exported scene to OBJ successfully")
        else:
            logging.warning("Scene loaded but contains no meshes.")
            raise ValueError("Loaded scene contains no meshes.")
    except Exception as e:
        logging.error(f"Error during conversion: {e}")
        raise

def show_mesh_with_texture(mesh_path, texture_content=None):
    def display_mesh():
        plotter = pv.Plotter()
        mesh = pv.read(mesh_path)
        if mesh.n_points == 0:
            logging.error("Empty meshes cannot be plotted. Input mesh has zero points.")
            return

        if texture_content:
            texture_path = os.path.join(TEXTURE_UPLOAD_FOLDER, 'temp_texture.jpg')
            with open(texture_path, 'wb') as texture_file:
                texture_file.write(texture_content)
            texture = pv.read_texture(texture_path)
            if 'Texture Coordinates' in mesh.point_data:
                texture_coords = mesh.point_data['Texture Coordinates']
                mesh.clear_textures()
                texture = pv.Texture(texture_path)
                mesh.point_data['Texture Coordinates'] = texture_coords
                mesh.textures['Texture Coordinates'] = texture
            plotter.add_mesh(mesh, texture=texture)
        else:
            plotter.add_mesh(mesh)

        plotter.show_axes()
        plotter.enable_terrain_style()
        plotter.add_camera_orientation_widget()
        plotter.show()

    threading.Thread(target=display_mesh).start()

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, server=server, url_base_pathname='/dash/', external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('3D Model Hub: Upload, View, and Download', className='text-center my-4')
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            html.H3('Source Files', className='text-center'),
            dcc.Dropdown(id='source-dropdown', placeholder='Select or Upload a Source File', className='mb-2'),
            dcc.Upload(
                id='upload-source',
                children=dbc.Button('Drag and Drop or Select a Source File', color='primary', className='btn-block mb-2'),
                style={'width': '100%', 'padding': '20px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'},
                multiple=False
            ),
            dbc.Button('Refresh Source List', id='refresh-source-button', color='secondary', className='btn-block')
        ], width=4, className='p-2'),

        dbc.Col([
            html.H3('Texture Files', className='text-center'),
            dcc.Dropdown(id='texture-dropdown', placeholder='Select or Upload a Texture File', className='mb-2'),
            dcc.Upload(
                id='upload-texture',
                children=dbc.Button('Drag and Drop or Select a Texture File', color='primary', className='btn-block mb-2'),
                style={'width': '100%', 'padding': '20px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'},
                multiple=False
            ),
            dbc.Button('Refresh Texture List', id='refresh-texture-button', color='secondary', className='btn-block')
        ], width=4, className='p-2'),

        dbc.Col([
            html.H3('Actions', className='text-center'),
            html.A(
                'Download Model', 
                id='download-model-button', 
                href='', 
                className='btn btn-primary btn-block mb-2'
            ),
            html.Div(id='message-box', className='border p-3 mb-2', style={'height': '200px', 'overflowY': 'scroll'})
        ], width=4, className='p-2')
    ]),

    dbc.Row([
        dbc.Col([
            html.H3('Viewer', className='text-center'),
            html.Div(id='viewer-message', className='border p-3 mb-2', style={'height': '100px', 'overflowY': 'scroll'})
        ], width=12, className='p-2'),

        dbc.Col([
            html.H3('Explanation', className='text-center'),
            html.Div(id='explanation-container', className='border p-3 mb-4', style={'height': '400px', 'overflowY': 'scroll'})
        ], width=12, className='p-2')
    ])
], fluid=True)

@app.callback(
    Output('download-model-button', 'href'),
    [Input('source-dropdown', 'value'), Input('texture-dropdown', 'value')]
)
def update_download_link(selected_source, selected_texture):
    if selected_source and selected_texture:
        obj_filename = f"{selected_source.split('.')[0]}.obj"
        texture_filename = selected_texture
        return f'/download-model/{obj_filename}/{texture_filename}'
    return ''

@app.callback(
    [Output('source-dropdown', 'options'),
     Output('texture-dropdown', 'options'),
     Output('viewer-message', 'children'),
     Output('message-box', 'children'),
     Output('explanation-container', 'children')],
    [Input('refresh-source-button', 'n_clicks'),
     Input('refresh-texture-button', 'n_clicks'),
     Input('upload-source', 'contents'),
     Input('upload-texture', 'contents'),
     Input('source-dropdown', 'value'),
     Input('texture-dropdown', 'value')],
    [State('upload-source', 'filename'),
     State('upload-texture', 'filename'),
     State('message-box', 'children')]
)
def update_content(refresh_source_clicks, refresh_texture_clicks, source_content, texture_content, selected_source, selected_texture, source_filename, texture_filename, current_messages):
    ctx = dash.callback_context
    messages = current_messages if current_messages else []
    viewer_message = []

    def log_message(message):
        logging.debug(message)
        messages.append(html.Div(message))

    def refresh_file_list():
        log_message("Refreshing file list")
        conn = get_db_connection()
        files = conn.execute('SELECT filename FROM files').fetchall()
        conn.close()
        log_message(f"Fetched {len(files)} source files")
        return [{'label': file['filename'], 'value': file['filename']} for file in files]

    def refresh_texture_list(selected_source):
        log_message("Refreshing texture list")
        conn = get_db_connection()
        textures = conn.execute('SELECT texture_filename FROM textures WHERE obj_filename = ?', (selected_source,)).fetchall()
        conn.close()
        log_message(f"Fetched {len(textures)} texture files for {selected_source}")
        return [{'label': 'View Only Mesh', 'value': 'view_only_mesh'}] + [{'label': texture['texture_filename'], 'value': texture['texture_filename']} for texture in textures]

    if not ctx.triggered:
        return refresh_file_list(), [], viewer_message, messages, get_explanations()

    trigger = ctx.triggered[0]['prop_id']

    try:
        if trigger == 'refresh-source-button.n_clicks':
            return refresh_file_list(), [], viewer_message, messages, get_explanations()

        elif trigger == 'refresh-texture-button.n_clicks':
            return refresh_file_list(), refresh_texture_list(selected_source), viewer_message, messages, get_explanations()

        elif trigger == 'upload-source.contents' and source_content is not None:
            content_type, content_string = source_content.split(',')
            decoded = base64.b64decode(content_string)
            filename = secure_filename(source_filename)

            if len(decoded) > MAX_CONTENT_LENGTH:
                log_message(f"File size exceeds the limit: {filename}")
                return refresh_file_list(), [], viewer_message, messages, get_explanations()

            original_format = os.path.splitext(filename)[1].lower()
            obj_content = None

            if original_format in ('.fbx', '.3ds', '.gltf', '.glb', '.dae', '.blend'):
                try:
                    input_path = os.path.join(TEMP_UPLOAD_FOLDER, filename)
                    with open(input_path, 'wb') as f:
                        f.write(decoded)
                    output_path = os.path.join(TEMP_UPLOAD_FOLDER, f"{os.path.splitext(filename)[0]}.obj")
                    convert_to_obj(input_path, output_path)
                    with open(output_path, 'rb') as f:
                        obj_content = f.read()
                except Exception as e:
                    log_message(f"Conversion failed: {e}")
                    return refresh_file_list(), [], viewer_message, messages, get_explanations()
            else:
                obj_content = decoded

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO files (filename, original_format, original_content, obj_content) VALUES (?, ?, ?, ?)', (filename, original_format, decoded, obj_content))
                conn.commit()

            log_message(f"Uploaded source file: {filename}")
            return refresh_file_list(), [], viewer_message, messages, get_explanations()

        elif trigger == 'upload-texture.contents' and texture_content is not None and selected_source is not None:
            content_type, content_string = texture_content.split(',')
            decoded = base64.b64decode(content_string)
            filename = secure_filename(texture_filename)

            if len(decoded) > MAX_CONTENT_LENGTH:
                log_message(f"File size exceeds the limit: {filename}")
                return refresh_file_list(), refresh_texture_list(selected_source), viewer_message, messages, get_explanations()

            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM textures WHERE texture_filename = ? AND obj_filename = ?', (filename, selected_source))
                link_exists = cursor.fetchone()[0] > 0
                if link_exists:
                    log_message(f"Texture file already linked to this source: {filename}")
                else:
                    cursor.execute('INSERT INTO textures (obj_filename, texture_filename, texture_content) VALUES (?, ?, ?)', (selected_source, filename, decoded))
                    conn.commit()
                    log_message(f"Uploaded texture file: {filename}")

            return refresh_file_list(), refresh_texture_list(selected_source), viewer_message, messages, get_explanations()

        elif trigger == 'source-dropdown.value' and selected_source is not None:
            return refresh_file_list(), refresh_texture_list(selected_source), viewer_message, messages, get_explanations()

        elif trigger == 'texture-dropdown.value' and selected_texture is not None:
            conn = get_db_connection()
            model = conn.execute('SELECT obj_content FROM files WHERE filename = ?', (selected_source,)).fetchone()
            texture = conn.execute('SELECT texture_content FROM textures WHERE texture_filename = ? AND obj_filename = ?', (selected_texture, selected_source)).fetchone()
            conn.close()
            if model is None:
                log_message("Model not found!")
                return refresh_file_list(), refresh_texture_list(selected_source), viewer_message, messages, get_explanations()

            obj_path = os.path.join(TEMP_UPLOAD_FOLDER, f"{selected_source.split('.')[0]}.obj")
            with open(obj_path, 'wb') as f:
                f.write(model['obj_content'])

            if texture and selected_texture != 'view_only_mesh':
                texture_path = os.path.join(TEXTURE_UPLOAD_FOLDER, selected_texture)
                with open(texture_path, 'wb') as f:
                    f.write(texture['texture_content'])
                show_mesh_with_texture(obj_path, texture['texture_content'])
            else:
                show_mesh_with_texture(obj_path)
            viewer_message = [html.Div("PyVista viewer opened in a new window")]
            return refresh_file_list(), refresh_texture_list(selected_source), viewer_message, messages, get_explanations()

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        log_message(error_message)
        return refresh_file_list(), refresh_texture_list(selected_source), viewer_message, messages, get_explanations()

    return refresh_file_list(), refresh_texture_list(selected_source), viewer_message, messages, get_explanations()

def get_explanations():
    explanations = [
        html.H3("Function Explanations"),
        html.H4("init_db"),
        html.P("Initialize the SQLite database with tables for storing files and textures."),
        
        html.H4("get_db_connection"),
        html.P("Get a connection to the SQLite database."),
        html.Ul([
            html.Li("Returns: sqlite3.Connection - The database connection.")
        ]),
        
        html.H4("index"),
        html.P("Redirect the root URL to the Dash app."),
        
        html.H4("serve_texture_file"),
        html.P("Serve the uploaded texture file."),
        html.Ul([
            html.Li("Args:"),
            html.Ul([
                html.Li("filename (str): The name of the texture file.")
            ]),
            html.Li("Returns:"),
            html.Ul([
                html.Li("Response: The file response.")
            ])
        ]),
        
        html.H4("convert_to_obj"),
        html.P("Convert a 3D file to OBJ format using Assimp."),
        html.Ul([
            html.Li("Args:"),
            html.Ul([
                html.Li("input_path (str): The path to the input file."),
                html.Li("output_path (str): The path to the output OBJ file.")
            ]),
            html.Li("Raises:"),
            html.Ul([
                html.Li("ValueError: If the scene contains no meshes."),
                html.Li("Exception: If an error occurs during conversion.")
            ])
        ]),
        
        html.H4("show_mesh_with_texture"),
        html.P("Display a 3D mesh with an optional texture using PyVista."),
        html.Ul([
            html.Li("Args:"),
            html.Ul([
                html.Li("mesh_path (str): The path to the mesh file."),
                html.Li("texture_content (bytes, optional): The content of the texture file.")
            ])
        ]),
        
        html.H4("update_content"),
        html.P("Callback function to update the content of the source and texture dropdowns, and to display the 3D model."),
        html.Ul([
            html.Li("Args:"),
            html.Ul([
                html.Li("refresh_source_clicks (int): Number of times the source list refresh button was clicked."),
                html.Li("refresh_texture_clicks (int): Number of times the texture list refresh button was clicked."),
                html.Li("source_content (str): Base64 encoded content of the uploaded source file."),
                html.Li("texture_content (str): Base64 encoded content of the uploaded texture file."),
                html.Li("selected_source (str): The selected source file from the dropdown."),
                html.Li("selected_texture (str): The selected texture file from the dropdown."),
                html.Li("source_filename (str): The filename of the uploaded source file."),
                html.Li("texture_filename (str): The filename of the uploaded texture file."),
                html.Li("current_messages (list): The current list of messages to be displayed.")
            ]),
            html.Li("Returns:"),
            html.Ul([
                html.Li("list: Updated options for the source dropdown."),
                html.Li("list: Updated options for the texture dropdown."),
                html.Li("list: Viewer message."),
                html.Li("list: Updated messages."),
                html.Li("list: Explanations for functions and usage.")
            ])
        ])
    ]
    return explanations




# Function to run the Dash server
def run_dash_server():
    app.run_server(debug=False, dev_tools_hot_reload=False, host='0.0.0.0')

# Function to open the Dash app in the default web browser
def open_browser():
    webbrowser.open_new_tab('http://localhost:8050/dash/')

if __name__ == "__main__":
    init_db() 
    # Start the Dash server in a separate thread
    dash_thread = threading.Thread(target=run_dash_server)
    dash_thread.start()
    
    # Wait for a moment to ensure that the server is up and running before opening the browser
    time.sleep(1)
    
    # Open the Dash app in the default web browser in another thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.start()
