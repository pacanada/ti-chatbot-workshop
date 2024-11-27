# Use the official Python 3.11 image as the base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the local directories into the container
COPY part_1/requirements.txt /app
# Install the required Python packages
RUN pip install -r requirements.txt
COPY part_1/txt_data /app/txt_data

COPY part_1/*.py /app/
# Expose the port for Chainlit
EXPOSE 8081

# Run the _get_text.py script and then the Chainlit server
CMD ["sh", "-c", "python3 _get_text.py && python -m chainlit run frontend.py -h --port 8081 --host 0.0.0.0"]
