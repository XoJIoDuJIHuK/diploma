FROM diploma-base

ENV PYTHONUNBUFFERED=1
#COPY contrib/docker/fastapi/docker-entrypoint.d /app/docker-entrypoint.d

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--timeout-keep-alive", "1", "--timeout-graceful-shutdown", "1"]
# CMD tail -f /dev/null
# CMD ["python", "-m", "debugpy", "--wait-for-client", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
