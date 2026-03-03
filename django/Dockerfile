ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-alpine

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

RUN chmod +x entry_point.sh

ENTRYPOINT ["./entry_point.sh"]
