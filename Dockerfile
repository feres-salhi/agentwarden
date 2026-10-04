FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY tools.py agent.py ./

RUN useradd --create-home agentuser
USER agentuser

ENTRYPOINT ["python", "agent.py"]