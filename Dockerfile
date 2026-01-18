# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy files needed for installation
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# Run the application
CMD ["uvicorn", "mcp_tim_wrapper.main:app", "--host", "0.0.0.0", "--port", "8080"]
