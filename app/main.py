from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import user


app = FastAPI()

origins = [
    'http://localhost:8000',
    'https://render-test-api-byr8.onrender.com'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(user.router)

@app.get('/')
async def index():
    return {'message': 'Hello World'}

@app.get('/privacy')
async def greet():
    return {'message': 'This is privacy page of Rin app.'}
