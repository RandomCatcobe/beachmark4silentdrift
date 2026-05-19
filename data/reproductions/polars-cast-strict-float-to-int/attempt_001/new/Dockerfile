FROM python:3.12-slim
WORKDIR /case
# Candidate: polars-cast-strict-float-to-int
# Side: new
# Intended dependency: polars==1.30.0
RUN python -m pip install polars==1.30.0
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
