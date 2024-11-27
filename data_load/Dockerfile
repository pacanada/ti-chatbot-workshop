# Use the specified image as the base image
FROM downloads.unstructured.io/unstructured-io/unstructured:0.10.19

# Set the working directory inside the container
WORKDIR /app

# Copy the local directories into the container
COPY data_load/requirements.txt /app
COPY data_load/*.py /app/

# Install the required Python packages
RUN pip install -r requirements.txt

# Run the extract_data.py script
CMD ["python3", "main.py"]
