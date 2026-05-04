"""
TIP: This is the main entry point of the FastAPI application. 
Implement the FastAPI app and integrate routers and databases here according to the README.
"""

from fastapi import FastAPI
from routes.data_ingestion import router as ingestionrouter
from routes.nlp_rag import router as nlproute


app = FastAPI()
app.include_router(ingestionrouter)
app.include_router(nlproute)

@app.get("/")
def root():
    return {"message": "FastAPI is running"}

