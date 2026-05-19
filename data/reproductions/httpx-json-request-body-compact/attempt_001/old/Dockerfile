FROM python:3.12-slim
WORKDIR /case
# Candidate: httpx-json-request-body-compact
# Side: old
# Intended dependency: httpx==0.27.2
RUN python -m pip install httpx==0.27.2
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
