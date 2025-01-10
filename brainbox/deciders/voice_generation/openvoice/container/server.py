import os
import uuid
import torch
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, UploadFile, File, Form

from openvoice import se_extractor
from openvoice.api import ToneColorConverter

CKPT_CONVERTER = 'checkpoints/converter'
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
OUTPUT_DIR = 'outputs'

app = FastAPI()

tone_color_converter = ToneColorConverter(
    f'{CKPT_CONVERTER}/config.json',
    device=DEVICE
)
tone_color_converter.load_ckpt(f'{CKPT_CONVERTER}/checkpoint.pth')  

@app.post("/generate")
async def generate_tts(
    source_speaker: UploadFile = File(...),
    reference_speaker: UploadFile = File(...)
):    
    try:
        id = uuid.uuid4()

        source_name, source_ext = os.path.splitext(source_speaker.filename)
        ref_name, ref_ext = os.path.splitext(reference_speaker.filename)

        output_path = f"{OUTPUT_DIR}/output_{id}.wav"

        source_path = f"{OUTPUT_DIR}/source_{id}{source_ext}"
        reference_path = f"{OUTPUT_DIR}/reference_{id}{ref_ext}"

        with open(source_path, "wb") as f:
            f.write(await source_speaker.read())
        with open(reference_path, "wb") as f:
            f.write(await reference_speaker.read())


        source_se, _ = se_extractor.get_se(
            source_path,
            tone_color_converter,
            vad=True
        )
        target_se, _ = se_extractor.get_se(
            reference_path,
            tone_color_converter,
            vad=True
        )

        encode_message = "@MyShell"

        tone_color_converter.convert(
            audio_src_path=source_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=output_path,
            message=encode_message
        )

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="failed")

        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=os.path.basename(output_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for file_path in [source_path, reference_path]:
            if os.path.exists(file_path):
                os.remove(file_path)