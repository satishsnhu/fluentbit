# ---------- FastAPI application ----------
FROM python:3.10-slim

# set up working directory
WORKDIR /app

# copy app code
COPY fastapi/ /app

# install dependencies
RUN pip install --no-cache-dir fastapi uvicorn gunicorn

# expose the app port
EXPOSE 80

# entrypoint (matches /start.sh in the tiangolo image you used locally)
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:80"]
