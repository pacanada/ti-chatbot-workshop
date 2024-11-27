# Use the official Python 3.11 image as the base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the local directories into the container
COPY part_2/requirements.txt /app
# Install the required Python packages
RUN pip install -r requirements.txt

COPY part_2/*.py /app/
# Expose the port for Chainlit
EXPOSE 9999

# Run the _get_text.py script and then the Chainlit server
CMD ["sh", "-c", "python -m chainlit run frontend.py -h --port 9999 --host 0.0.0.0"]
