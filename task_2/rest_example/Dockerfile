# Use base Python image
FROM python:3.12.6

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY rest_example/pyproject.toml rest_example/poetry.lock ./

# Install dependencies via Poetry (without creating a virtual environment)
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application files
COPY rest_example /app/rest_example

# Set the PYTHONPATH environment variable
ENV PYTHONPATH="/app"

# Run the FastAPI application with uvicorn
CMD ["uvicorn", "rest_example.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
