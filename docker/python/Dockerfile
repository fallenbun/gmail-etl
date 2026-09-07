FROM python:3.14

WORKDIR /src

RUN apt-get update \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#COPY src/ .
CMD ["python3", "-u", "main.py"]