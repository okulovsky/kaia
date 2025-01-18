import os
import subprocess
import logging
import traceback

import flask
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/uploads'
OUTPUT_FOLDER = '/outputs'

class DenoiserApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/enhance', view_func=self.enhance_audio, methods=['POST'])

    def create_app(self):
        return self.app

    def index(self):
        return "OK"

    def enhance_audio(self):
        try:
            filename = request.json['filename']
            subprocess.run([
                '/home/app/.local/bin/resemble-enhance',
                UPLOAD_FOLDER,
                OUTPUT_FOLDER,
                ],
                check=True,
            )
        except:
            return traceback.format_exc(), 500

