FROM apache/airflow:3.3.1
USER root
COPY requirements.txt .
RUN apt-get update \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
USER $AIRFLOW_UID
RUN pip install --no-cache-dir -r requirements.txt