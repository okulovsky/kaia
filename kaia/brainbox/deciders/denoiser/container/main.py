import uvicorn
from server import DenoiserApp

app = DenoiserApp().create_app()

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)