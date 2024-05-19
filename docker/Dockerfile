# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy the pyproject.toml and poetry.lock files
COPY ./pyproject.toml ./poetry.lock ./
COPY ./aas_middleware ./aas_middleware

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Copy the rest of the application code
COPY ./docker/docker_app.py ./

# Expose the port FastAPI will run on
EXPOSE 8000

# # Command to run the application
CMD ["uvicorn", "docker_app:app", "--host", "0.0.0.0", "--port", "8000"]
