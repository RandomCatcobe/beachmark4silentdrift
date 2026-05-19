FROM python:3.12-slim
WORKDIR /case
# Candidate: pandas-timestamp-to-datetime64-resolution
# Side: new
# Intended dependency: pandas==2.0.3
RUN python -m pip install numpy==1.24.4 pandas==2.0.3
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
