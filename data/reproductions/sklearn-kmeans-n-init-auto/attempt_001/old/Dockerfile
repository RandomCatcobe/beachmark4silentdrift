FROM python:3.12-slim
WORKDIR /case
# Candidate: sklearn-kmeans-n-init-auto
# Side: old
# Intended dependency: scikit-learn==1.3.2
RUN python -m pip install scikit-learn==1.3.2
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
