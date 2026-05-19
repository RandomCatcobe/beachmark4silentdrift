FROM python:3.12-slim
WORKDIR /case
# Candidate: numpy-choice-shuffle-with-p
# Side: old
# Intended dependency: numpy==2.3.4
RUN python -m pip install numpy==2.3.4
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
