# ti-chatbot-workshop
Repository used for the T&amp;I conference: **Smart Chatbot Workshop**

## Run part 1

0. Be in the office or connect with a VPN to DFDS network
1. Copy the `.env.example` file to `.env` and fill in the required values from 1Password
2. Setup: Run `docker-compose up --build part_1`:
    - Exercise 0: Check UI in localhost:8081 and ask any question related to Poland
    - Exercise 1: Include your own files in `part_1/txt_data/` to be used for RAG
    - Exercise 2: Add a welcome message: `part_1/frontend.py`
    - Exercise 3: Modify assistant system message in: `part_1/chatbot.py`
    - Exercise 4: Adjust number of retrieved documents in `part_1/chatbot.py`

## Run part 2

Before running make sure that you have configured LF line endings for all the files!!!

```bash
docker pull downloads.unstructured.io/unstructured-io/unstructured:0.10.19
```

To execute the part 2 with default data run:
```bash
docker compose up data_load
docker compose up part_2
```

## Add the data to the VectorDB for multimodal chatbot

You can add the data by moving your files to the `data_load/data/Raw Documents` folder and running the `data_load` service.

```bash
docker compose up data_load
```
You can edit the `data_load/main.py` script and other scripts in the `data_load` folder to change the code. 

To apply these changes:
1. Modify the entry command in the Dockerfile to run indefinitely (commented out part).
2. Copy the updated files to the running container.
3. Run the scripts inside the container.


Replace `container_id` with the ID of the container running the `data_load` service. If you want the service to keep running, ensure the entry command in the Dockerfile is set to run indefinitely.
Copy a file:

```bash
docker cp ./data_load/main.py container_id:/app/main.py
```

Run the script:

```bash
docker exec -it container_id python3 /app/main.py
```

The alternative to copying the files is to edit them and run:

```bash
docker compose down data_load -v
docker compose up data_load --build
```


To run part 2 after adding new data:
```bash
docker-compose up part_2
```

Check UI in localhost:9999 and ask any question related to London.

## Remove everything
To remove everything:

```bash
docker compose down -v
```

Remove unstructured.io image:

```bash
docker rmi downloads.unstructured.io/unstructured-io/unstructured:0.10.19
```