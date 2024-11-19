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

# Generate a random string to use as the file name
def generate_random_filename(extension):
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"{random_string}.{extension}"

@app.route('/')
def index():
    # Get list of uploaded images and QR codes
    image_files = os.listdir(app.config['UPLOAD_FOLDER'])
    qr_files = os.listdir(app.config['QR_FOLDER'])
    return render_template("index.html", image_files=image_files, qr_files=qr_files)

@app.route('/capture')
def capture():
    # Render a page with camera functionality
    return render_template('capture.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # Generate a random file name
        extension = file.filename.rsplit('.', 1)[1].lower()  # Get the file extension (e.g., 'png')
        random_filename = generate_random_filename(extension)
        
        # Save the uploaded image with the random filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], random_filename)
        file.save(filepath)

        # Get the local IP address of the server
        local_ip = get_local_ip()
        # Construct the image URL with the local IP address
        image_url = f"http://{local_ip}:5000/uploads/{random_filename}"
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

# if __name__ == '__main__':
#     # Run the server on the local IP address
#     app.run(debug=True, host="0.0.0.0", port=5000)
