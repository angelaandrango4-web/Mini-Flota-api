from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def healt_check():
    return{"status": "ok"}


