FROM python:3.12-slim
WORKDIR /case
# Candidate: httpx-json-request-body-compact
# Side: new
# Intended dependency: httpx==0.28.0
RUN python -m pip install httpx==0.28.0
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
