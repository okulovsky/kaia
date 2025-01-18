import uvicorn
from server import DenoiserApp


if __name__ == '__main__':
    DenoiserApp().create_app().run('0.0.0.0', 8080)