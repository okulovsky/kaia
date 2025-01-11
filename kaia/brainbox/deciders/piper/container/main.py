import subprocess, sys

subprocess.run([
    sys.executable, 
    "-m", "uvicorn", 
    "app.server:app", 
    "--host", "0.0.0.0", 
    "--port", "8080"
])
