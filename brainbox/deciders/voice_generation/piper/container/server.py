from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os 
from pathlib import Path
import subprocess
import uuid
from fastapi.responses import FileResponse

app = FastAPI()

AUDIO_OUTPUT_DIR = "/audio_files"  
MODEL_DIR = "../config"              

class TTSRequest(BaseModel):
    text: str
    model_path: str 

class ModelDownloadRequest(BaseModel):
    name: str
    config_url: str        
    url: str    

@app.get("/")
async def read_root():
    return "OK"

@app.post("/download_model")
async def download_model(request: ModelDownloadRequest):
    model_path = os.path.join(MODEL_DIR, f"{request.name}.onnx")
    config_path = os.path.join(MODEL_DIR, f"{request.name}.onnx.json")
    
    download_model_cmd = f'wget -O {model_path} "{request.url}"'
    download_config_cmd = f'wget -O {config_path} "{request.config_url}"'

    try:
        subprocess.run(
            ["sh", "-c", download_model_cmd],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        subprocess.run(
            ["sh", "-c", download_config_cmd],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return {"message": f"model '{request.name}' downloaded"}
    
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode().strip() if e.stderr else "undefined"
        raise HTTPException(status_code=500, detail=error_msg) from e
    
@app.get("/list_models")
async def list_models():
    command = f'find {MODEL_DIR} -maxdepth 1 -type f -name "*.onnx"'

    try:
        result = subprocess.run(
            ["sh", "-c", command],
            capture_output=True,
            text=True,
            check=True,
        )
        models = result.stdout.strip().split('\n')
        
        models = [model for model in models if model]
        
        return {"models": models}
    
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="error with getting message") from e
    
@app.post("/synthesize")
async def synthesize_text(request: TTSRequest):
    audio_filename = f"{uuid.uuid4()}.wav"
    container_audio_path = f"{AUDIO_OUTPUT_DIR}/{audio_filename}"

    command = f'echo "{request.text}" | /usr/share/piper/piper --model {request.model_path} --output_file {container_audio_path}'
    
    try:
        subprocess.run(
            ["sh", "-c", command],
            check=True,
        )

        return FileResponse(
            path=container_audio_path,
            media_type="audio/wav",
            filename=audio_filename
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="error with generating") from e