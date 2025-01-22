# Start with a base image containing Python 3.13
FROM python:3.13-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy the necessary files
COPY pyproject.toml /app/
COPY src /app/src

# Install dependencies
RUN pip install --upgrade pip && \
    pip install hatch && \
    hatch build && \
    pip install dist/*.whl

# Expose any ports if needed (not specified in README, assumed none)
# EXPOSE 8000

# Command to run the server
CMD ["python", "src/mcp_jira_python/server.py"]
