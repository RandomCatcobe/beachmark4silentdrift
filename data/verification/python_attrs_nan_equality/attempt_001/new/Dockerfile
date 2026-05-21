FROM python:3.12-slim
WORKDIR /case
# Candidate: py-attrs-nan-equality
# Side: new
# Intended dependency: attrs==24.1.0
RUN python -m pip install attrs==24.1.0
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
