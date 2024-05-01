from fastapi import FastAPI

from routes import search

app = FastAPI()

app.include_router(search.router)
