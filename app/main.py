from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import webhook


app = FastAPI()

origins = [
    'http://localhost:8000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(webhook.router)

@app.get('/')
async def index():
    return {'message': 'Hello World'}

@app.get('/privacy')
async def greet():
    return {'message': 'This is privacy page of Rin app.'}
