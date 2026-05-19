FROM python:3.12-slim
WORKDIR /case
# Candidate: sklearn-kmeans-n-init-auto
# Side: new
# Intended dependency: scikit-learn==1.5.2
RUN python -m pip install scikit-learn==1.5.2
COPY client.py /case/client.py
CMD ["python", "/case/client.py"]
