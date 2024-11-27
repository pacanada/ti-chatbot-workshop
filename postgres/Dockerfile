# Use the updated pgvector image as the base image
FROM pgvector/pgvector:pg16

# Set environment variables
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=postgres
ENV TZ=Europe/Copenhagen

# Copy the initialization script into the container
COPY init-db.sh /docker-entrypoint-initdb.d/

# Ensure the script is executable
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh

# Expose the PostgreSQL port
EXPOSE 5432