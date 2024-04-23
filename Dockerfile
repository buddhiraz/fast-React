# Step 1: Node image to build React frontend
FROM node:16 as build-stage

WORKDIR /app

COPY frontend/package*.json ./

RUN npm install

COPY frontend/ .

# Build the application
RUN npm run build

# Step 2: Python image to run FastAPI backend
FROM python:3.10

WORKDIR /code

# Copy the built React app from the build-stage
COPY --from=build-stage /app/build /code/frontend/build

# Copy the FastAPI application files
COPY main.py requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload"]
