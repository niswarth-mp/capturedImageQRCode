import os
import random
import string
import socket
from flask import Flask, request, jsonify, send_from_directory, render_template

import qrcode

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
QR_FOLDER = "qr_codes"

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['QR_FOLDER'] = QR_FOLDER

# Function to get the local IP address
def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# Function to generate a number-based filename for the uploaded image
def generate_numbered_filename():
    # Generate a number-based filename (e.g., 1.jpg, 2.png, etc.)
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    last_number = 0
    for file in files:
        if file.endswith(('.jpg', '.jpeg', '.png', '.gif')):  # Filter image files
            try:
                number = int(os.path.splitext(file)[0])  # Get the number from the filename
                last_number = max(last_number, number)
            except ValueError:
                continue
    new_number = last_number + 1
    return f"{new_number}.jpg"  # You can adjust the file extension as needed

@app.route('/')
def index():
    # Get list of uploaded images
    image_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template("index.html", image_files=image_files)

@app.route('/capture')
def capture():
    # Render a page with camera functionality
    return render_template('capture.html')

@app.route('/gallery')
def gallery():
    # Get list of uploaded images
    image_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template("gallery.html", image_files=image_files)

@app.route('/viewGallery')
def viewgallery():
    # Get list of uploaded images
    image_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template("viewGallery.html", image_files=image_files)
    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # Extract and validate the file extension
        if '.' in file.filename:
            extension = file.filename.rsplit('.', 1)[1].lower()
        else:
            return jsonify({'error': 'Invalid file extension'}), 400

        # Generate a numbered filename (e.g., 1.jpg, 2.jpg, etc.)
        random_filename = generate_numbered_filename()

        # Save the uploaded image with the numbered filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], random_filename)
        file.save(filepath)

        # Use the fixed URL for the image
        image_url = f"https://capturedimageqrcode-2.onrender.com/uploads/{random_filename}"
        
        # Generate a QR code for the image URL
        qr_code_path = generate_qr_code(image_url, random_filename)

        return jsonify({
            'image_url': f'/uploads/{random_filename}',
            'qr_code_url': f'/qr_codes/{os.path.basename(qr_code_path)}'
        })

    return jsonify({'error': 'File upload failed'}), 500

def generate_qr_code(data, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)

    qr_code_img = qr.make_image(fill_color="black", back_color="white")
    qr_code_path = os.path.join(app.config['QR_FOLDER'], f'{os.path.splitext(filename)[0]}_qr.png')
    qr_code_img.save(qr_code_path)
    return qr_code_path

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/qr_codes/<filename>')
def serve_qr_code(filename):
    return send_from_directory(app.config['QR_FOLDER'], filename)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    # Delete uploaded image
    uploaded_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    qr_file_path = os.path.join(app.config['QR_FOLDER'], f"{os.path.splitext(filename)[0]}_qr.png")

    if os.path.exists(uploaded_file_path):
        os.remove(uploaded_file_path)
    else:
        return jsonify({'error': 'Image file not found'}), 404

    # Delete corresponding QR code file
    if os.path.exists(qr_file_path):
        os.remove(qr_file_path)

    return jsonify({'success': True}), 200

if __name__ == '__main__':
    # Run the server on the local IP address
    app.run(debug=True, host="0.0.0.0", port=5000)
