import os
import subprocess
import logging
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from ..settings import DenoiseSettings

class DenoiserApp:
    def __init__(self):
        self.settings = DenoiseSettings()
        self.app = Flask(__name__)
        self.app.config['UPLOAD_FOLDER'] = self.settings.upload_folder
        self.app.config['OUTPUT_FOLDER'] = self.settings.output_folder
        os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(self.app.config['OUTPUT_FOLDER'], exist_ok=True)

        self._setup_routes()

    def create_app(self):
        return self.app

    def _setup_routes(self):
        self.app.route('/enhance', methods=['POST'])(self.enhance_audio)
        self.app.route('/downloads/<filename>', methods=['GET'])(self.download_file)

    def enhance_audio(self):
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files part'}), 400

        files = request.files.getlist('files[]')
        processed_filenames = []

        for file in files:
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                try:
                    subprocess.run(['resemble_enhance', file_path, self.app.config['OUTPUT_FOLDER']], check=True)
                    logging.info(f"Successfully processed: {filename}")
                    processed_filenames.append(filename)
                    os.remove(file_path)
                except subprocess.CalledProcessError as e:
                    logging.error(f"Error processing {filename}: {e}")
                    return jsonify({'error': f'Error processing {filename}: {e}'}), 500
                except FileNotFoundError:
                    logging.error(f"Error: resemble_enhance script not found.")
                    return jsonify({'error': 'resemble_enhance script not found'}), 500

        processed_file_urls = [f'/downloads/{filename}' for filename in processed_filenames]
        return jsonify({'processed_files': processed_file_urls}), 200

    def download_file(self, filename):
        return send_from_directory(self.app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in DenoiseSettings().allowed_extensions