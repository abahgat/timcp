# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY pyproject.toml .

# Install any needed packages specified in pyproject.toml
RUN pip install --no-cache-dir .

# Copy the rest of the application's code to the working directory
COPY src/ /app/src

# Run the application
CMD ["uvicorn", "mcp_tim_wrapper.main:app", "--host", "0.0.0.0", "--port", "8080"]
