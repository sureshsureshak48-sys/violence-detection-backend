FROM python:3.9-slim

# Install system dependencies (OpenCV requires libGL)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 5000 for Flask (HuggingFace Docker spaces map port 7860 by default, 
# so we will run flask on 7860)
EXPOSE 7860

# Command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=7860"]
