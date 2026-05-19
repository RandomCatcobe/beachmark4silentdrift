FROM python:3.12-slim
WORKDIR /case
# Candidate: pandas-timestamp-to-datetime64-resolution
# Side: old
# Intended dependency: pandas==1.5.3
RUN python -m pip install numpy==1.24.4 pandas==1.5.3
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
