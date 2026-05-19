FROM python:3.12-slim
WORKDIR /case
# Candidate: pydantic-optional-field-required
# Side: old
# Intended dependency: pydantic==1.10.15
RUN python -m pip install pydantic==1.10.15
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
