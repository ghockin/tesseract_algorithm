from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename

# Initialize the Flask application
app = Flask(__name__)

# Define the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'  # Save directly in static/uploads folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure app to use the upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Box data will be stored here for the session
box_data = []

# Function to check if the file has a valid extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    uploaded_filename = None
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        
        # If the user does not select a file, the browser submits an empty part without a filename
        if file.filename == '':
            return redirect(request.url)
        
        # If the file is allowed, save it directly to the static folder
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            uploaded_filename = filename
    
    return render_template('index.html', uploaded_filename=uploaded_filename, boxes=box_data)

@app.route('/save_boxes', methods=['POST'])
def save_boxes():
    global box_data
    # Get the box data from the request
    data = request.get_json()
    box_data = data['boxes']  # Store the box data
    
    # Return the updated box data as a JSON response
    return jsonify({'boxes': box_data})

if __name__ == '__main__':
    app.run(debug=True)
