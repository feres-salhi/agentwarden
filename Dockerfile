FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir anthropic==1.11.0 python-dotenv==1.2.4

COPY tools.py agent.py ./

RUN useradd --create-home agentuser
USER agentuser

ENTRYPOINT ["python", "agent.py"]