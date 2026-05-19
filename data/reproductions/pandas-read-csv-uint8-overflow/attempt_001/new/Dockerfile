FROM python:3.12-slim
WORKDIR /case
# Candidate: pandas-read-csv-uint8-overflow
# Side: new
# Intended dependency: pandas==2.1.1
RUN python -m pip install numpy==1.26.0 pandas==2.1.1
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
