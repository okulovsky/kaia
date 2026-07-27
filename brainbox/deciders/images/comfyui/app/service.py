from interface import IComfyUI
from foundation_kaia.marshalling import JSON, FileLike, FileLikeHandler
import requests
import time
import tarfile
import json
import uuid
from io import BytesIO
from pathlib import Path

COMFY_URL = 'http://127.0.0.1:8188'
INPUT_PATH = Path('/home/app/comfy/ComfyUI/input')
CLIENT_ID = 'internal_brainbox_client'

def _run_workflow_and_return_contents(prompt) -> dict[str, bytes]:
    r = requests.post(
        f"{COMFY_URL}/prompt",
        json={
            "prompt": prompt,
            "client_id": CLIENT_ID,
        },
    )
    if r.status_code != 200:
        raise ValueError(f"Comfy rejected the workflow:\n{r.json()}")

    prompt_id = r.json()["prompt_id"]

    while True:
        history = requests.get(f"{COMFY_URL}/history/{prompt_id}").json()
        if prompt_id in history:
            break
        time.sleep(1)

    outputs = history[prompt_id]["outputs"]

    output_contents = {}

    for node_id, node_output in outputs.items():
        for image in node_output.get("images", []):
            params = {
                "filename": image["filename"],
                "subfolder": image["subfolder"],
                "type": image["type"],
            }

            img = requests.get(f"{COMFY_URL}/view", params=params)
            img.raise_for_status()

            output_contents[image['filename']] = img.content
    return output_contents



class ComfyUIService(IComfyUI):
    def workflow(self,
                 workflow: JSON,
                 input_0: FileLike|None = None,
                 input_1: FileLike|None = None,
                 input_2: FileLike|None = None,
                 input_3: FileLike|None = None,
                 input_4: FileLike|None = None,
                 ) -> FileLike:
        # Inputs are written under a fresh unique filename each call, and that filename
        # replaces the generic placeholder inside the workflow graph, so ComfyUI's own
        # execution cache can't mistake a new image for a previously-seen one just because
        # it landed at the same fixed path (see git history for the bug this fixes).
        workflow_text = json.dumps(workflow)
        written_paths = []
        try:
            for index, input in enumerate([input_0, input_1, input_2, input_3, input_4]):
                if input is not None:
                    unique_filename = f"input_{index}_{uuid.uuid4().hex}"
                    path = INPUT_PATH/unique_filename
                    FileLikeHandler.write(input, path)
                    written_paths.append(path)
                    workflow_text = workflow_text.replace(IComfyUI.input_placeholder(index), unique_filename)

            contents = _run_workflow_and_return_contents(json.loads(workflow_text))
            if len(contents) == 1:
                key = list(contents.keys())[0]
                return contents[key]

            buffer = BytesIO()
            with tarfile.open(fileobj=buffer, mode='w') as tar:
                for filename, content in contents.items():
                    info = tarfile.TarInfo(name=filename)
                    info.size = len(content)
                    tar.addfile(info, BytesIO(content))
            return buffer.getvalue()
        finally:
            for path in written_paths:
                path.unlink(missing_ok=True)


