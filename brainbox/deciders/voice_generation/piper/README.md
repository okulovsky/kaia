python -m kaia.brainbox.deciders.piper.run

дата пример:

/download_model
{
  "name": "en_GB-alba-medium",
  "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json?download=true",
  "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alba/medium/en_GB-alba-medium.onnx"
} 

/synthesize
{
  "text": "Hello! My name is Alba. I am 15 years old.",
  "model_path": "/config/en_GB-alba-medium.onnx"
}


