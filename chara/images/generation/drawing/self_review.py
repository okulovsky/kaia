from brainbox.deciders import Ollama
from .case import DrawingCase

MODEL_NAME = 'qwen2.5vl:7b'

PROMPT = '''
Please analyze this image and answer the following questions:
* `one_person`: does this picture depicts exactly one person?
* `anatomy`: does this picture depicts the anatomy correctly? Rate from 0 (bad anatomy) to 10 (good anatomy)
* `face`: does this picture depicts the face properly? Since it's anime, the face is not expected to be realistic, but some standards need to be maintained. Rate from 0 (bad face) to 10 (good face), or null if the face not visible.
* `overall`: can this picture be considered as a good image? Rate from 0 (bad image) to 10 (good image).

Please provide the answer in the JSON format, for example: 

```
{
"one_person": true,
"anatomy": 6,
"face": null,
"overall": 7
}
```
'''

def create_self_review_task(case: DrawingCase):
    return Ollama.new_task(parameter=MODEL_NAME).question(
        PROMPT,
        image=case.image.name
    )