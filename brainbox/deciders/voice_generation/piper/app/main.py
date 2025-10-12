import subprocess, sys
from pathlib import Path

subprocess.run([
    sys.executable, 
    "-m", "uvicorn", 
    "server:app",
    "--host", "0.0.0.0", 
    "--port", "8080"
], cwd =  Path(__file__).parent)
