FROM python:3.12-slim
WORKDIR /case
# Candidate: py-attrs-nan-equality
# Side: old
# Intended dependency: attrs==23.2.0
RUN python -m pip install attrs==23.2.0
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
