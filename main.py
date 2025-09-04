from fastapi import FastAPI
from document_process import doc_process

app = FastAPI()

app.include_router(doc_process)
