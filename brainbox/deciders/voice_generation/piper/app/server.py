import traceback

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os 
from pathlib import Path
import subprocess
import uuid
from fastapi.responses import FileResponse

app = FastAPI()

AUDIO_OUTPUT_DIR = Path('/cache')
MODEL_DIR = Path("/models")


class TTSRequest(BaseModel):
    text: str
    model: str
    noise_scale: float|None
    length_scale: float|None
    noise_w: float|None
    speaker: int|None

class ModelDownloadRequest(BaseModel):
    name: str
    config_url: str        
    url: str    

@app.get("/")
async def read_root():
    return "OK"


@app.post("/synthesize")
async def synthesize_text(request: TTSRequest):
    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
    id = str(uuid.uuid4())
    text_filename = AUDIO_OUTPUT_DIR/f'{id}.txt'
    container_audio_path = AUDIO_OUTPUT_DIR/f"{id}.wav"
    try:
        model_path = os.path.join(MODEL_DIR, request.model + ".onnx")
        #TODO:
        #It works and it works fast enough, but how? Does it keep the model in memory for the next calls?
        #If not, can we somehow preload this model to make it even faster?
        with open(text_filename,'w') as stream:
            stream.write(request.text)
        command = [f'cat {text_filename} | /lsiopy/bin/piper --model {model_path} --output_file {container_audio_path}']
        for option in ['noise_scale', 'length_scale', 'noise_w','speaker']:
            value = getattr(request, option)
            if value is not None:
                command.append(f' --{option} {value}')
        command = ' '.join(command)

        try:
            subprocess.check_output(["sh", "-c", command])
        except subprocess.CalledProcessError as ex:
            raise ValueError(f"Exception when called\n{command}\n\nThe error: {ex.output}")

        return FileResponse(
            path=container_audio_path,
            media_type="audio/wav",
            filename=container_audio_path.name
        )
    except:
        raise HTTPException(status_code=500, detail=traceback.format_exc())
    finally:
        pass