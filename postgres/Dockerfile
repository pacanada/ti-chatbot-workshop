# Use the updated pgvector image as the base image
FROM pgvector/pgvector:pg16

# Set environment variables
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=postgres
ENV TZ=Europe/Copenhagen

# Copy the initialization script into the container
COPY init-db.sh /docker-entrypoint-initdb.d/

# Copy the dump file to a different directory
COPY dump-postgres-202411251007.sql /opt/dump-postgres.sql

# Ensure the script is executable
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh

# Expose the PostgreSQL port
EXPOSE 5432