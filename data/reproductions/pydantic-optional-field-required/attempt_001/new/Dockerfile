FROM python:3.12-slim
WORKDIR /case
# Candidate: pydantic-optional-field-required
# Side: new
# Intended dependency: pydantic==2.7.4
RUN python -m pip install pydantic==2.7.4
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
