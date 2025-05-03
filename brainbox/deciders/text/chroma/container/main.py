import uvicorn
from server import Retriever

app = Retriever().create_app()

if __name__ == '__main__':
    uvicorn.run(f"main:app", host='0.0.0.0', port=5252, reload=True)