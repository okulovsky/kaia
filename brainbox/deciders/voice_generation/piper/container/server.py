import traceback

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os 
from pathlib import Path
import subprocess
import uuid
from fastapi.responses import FileResponse

app = FastAPI()

AUDIO_OUTPUT_DIR = '/cache'
MODEL_DIR = "/models"

class TTSRequest(BaseModel):
    text: str
    model: str

class ModelDownloadRequest(BaseModel):
    name: str
    config_url: str        
    url: str    

@app.get("/")
async def read_root():
    return "OK"


@app.post("/synthesize")
async def synthesize_text(request: TTSRequest):
    try:
        audio_filename = f"{uuid.uuid4()}.wav"
        os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
        container_audio_path = f"{AUDIO_OUTPUT_DIR}/{audio_filename}"

        model_path = os.path.join(MODEL_DIR, request.model + ".onnx")

        #TODO:
        #It works and it works fast enough, but how? Does it keep the model in memory for the next calls?
        #If not, can we somehow preload this model to make it even faster?
        command = f'echo "{request.text}" | /usr/share/piper/piper --model {model_path} --output_file {container_audio_path}'

        subprocess.run(
            ["sh", "-c", command],
            check=True,
        )

        return FileResponse(
            path=container_audio_path,
            media_type="audio/wav",
            filename=audio_filename
        )
    except:
        raise HTTPException(status_code=500, detail=traceback.format_exc())