FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app
# Install dependencies using Poetry
RUN pip install aas2openapi
# TODO: use repository and poetry and not pip install

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "docker_app:middleware.app", "--host", "0.0.0.0", "--port", "8000"]