from fastapi import FastAPI
import logging, sys

logger = logging.getLogger("uvicorn")
handler = logging.StreamHandler(sys.stdout)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = FastAPI()

@app.get("/")
def root():
    logger.info("user=jane.doe@example.com, ssn=123-45-6789, phone=732-555-1212")
    return {"msg": "hello"}
