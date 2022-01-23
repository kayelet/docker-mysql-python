# Use an official Python runtime as an image
FROM python:3.9

WORKDIR /app

# Install Flask & mysql-connector
COPY requirements.txt .
RUN pip install -r requirements.txt

# Run app.py (Flask) when the container launches allowing sql info by API routes
RUN mkdir templates
COPY *.py .
COPY templates/index.html templates/
CMD ["python", "app.py" ]