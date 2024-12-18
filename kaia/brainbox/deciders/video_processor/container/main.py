import uvicorn
from server import VideoProcessorApp

app = VideoProcessorApp().create_app()

if __name__ == '__main__':
    uvicorn.run(f"main:app", host="0.0.0.0", port=8084, reload=True)
