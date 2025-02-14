import os
import subprocess
import logging
import traceback

import flask
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import torch
from resemble_enhance.enhancer.inference import denoise, enhance
import torchaudio


UPLOAD_FOLDER = '/uploads'
OUTPUT_FOLDER = '/outputs'

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

class DenoiserApp:

    def create_app(self):
        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/enhance', view_func=self.enhance_audio, methods=['POST'])
        return self.app

    def index(self):
        return "OK"

    def enhance_audio(self):
        try:
            filename = request.json['filename']
            solver = request.json.get('solver', 'Midpoint') #"CFM ODE Solver", Options ["Midpoint", "RK4", "Euler"]
            nfe = request.json.get('nfe', 64) #"CFM Number of Function Evaluations", from 1 to 128
            tau = request.json.get('tau', 0.5) #"CFM Prior Temperature", from 0 to 1
            denoising = request.json.get('denoising', False) #Denoise before enhancement

            path = os.path.join(UPLOAD_FOLDER, filename)

            solver = solver.lower()
            nfe = int(nfe)
            lambd = 0.9 if denoising else 0.1

            dwav, sr = torchaudio.load(path)
            dwav = dwav.mean(dim=0)

            wav1, new_sr = denoise(dwav, sr, device)
            wav2, new_sr = enhance(dwav, sr, device, nfe=nfe, solver=solver, lambd=lambd, tau=tau)

            wav1 = wav1.cpu().numpy()
            wav2 = wav2.cpu().numpy()

            wav1 = torch.from_numpy(wav1).unsqueeze(0)
            wav2 = torch.from_numpy(wav2).unsqueeze(0)

            denoised_name = filename+'.denoised.wav'
            torchaudio.save(os.path.join(OUTPUT_FOLDER, denoised_name), wav1, new_sr)
            enhanced_name = filename+'.enhanced.wav'
            torchaudio.save(os.path.join(OUTPUT_FOLDER, enhanced_name), wav2, new_sr)
            return flask.jsonify([denoised_name, enhanced_name])
        except:
            return traceback.format_exc(), 500


