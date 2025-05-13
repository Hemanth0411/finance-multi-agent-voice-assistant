# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Default EXPOSE (Orchestrator) - others are exposed by docker-compose
EXPOSE 8000

# Expose ports for other agents if running in the same container (Not recommended for production)
EXPOSE 8001
EXPOSE 8002
# EXPOSE 8003
# EXPOSE 8004

# Define environment variable (Optional)
# ENV NAME World

# Command to run the orchestrator application using uvicorn
# This will start the orchestrator. To run other agents, you'd need
# a different CMD, an entrypoint script, or a process manager like supervisord.
# For Day 1, we focus on running the orchestrator primarily.
CMD ["uvicorn", "orchestrator.app:app", "--host", "0.0.0.0", "--port", "8000"]

# To run individual agents (Example):
# CMD ["uvicorn", "agents.api_agent.app:app", "--host", "0.0.0.0", "--port", "8001"]
# CMD ["uvicorn", "agents.retriever_agent.app:app", "--host", "0.0.0.0", "--port", "8002"]
