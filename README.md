# Introduction

Welcome to LLM Chatbot demo!

# Getting Started

## Install Poetry/Virtualenv

Shell:

```bash
poetry config virtualenvs.in-project true
poetry env use python
. .venv/bin/activate
poetry install
````

Powershell:

```bash
poetry config virtualenvs.in-project true
poetry env use python
.\.venv\Scripts\activate.ps1
poetry install
```

Run notebooks

```bash
python -m ipykernel install --user --name=myenv --display-name "Python (.venv)"
jupyter notebook
```

## Add stuff to the `.env` file

Add config from the `.env.example` file and from 1Password to the `.env` file

```bash
touch .env
```

## Run docker-compose

Before running make sure that you have configured LF line endings for all the files in the `local`
folder!!!

```bash
docker pull downloads.unstructured.io/unstructured-io/unstructured:0.10.19
```

```bash
docker-compose up --build
```

To remove everything:

```bash
docker compose down -v
```

Remove unstructured.io image:

```bash
docker rmi downloads.unstructured.io/unstructured-io/unstructured:0.10.19
```

## Add the data to the VectorDB for multimodal chatbot

You will need to replace the container id with the one that is running the data_load service, if you want to have it running you have to switch the entry command in the Dockerfile

```bash
docker compose up data_load
```

You can edit the data_load/main.py script and other scripts in data_load folder to change the code.
Once you switch to the entry command in the Dockerfile to run indefinitely you can copy the updated files to the container and run the scripts.

copy all files:

```bash
docker cp ./data_load 15c9450a50783d6e58dcf3f39b0b680c45fdf4686e4bae653b75bf2d59840704:/app
```

copy one file:

```bash
docker cp ./data_load/main.py 15c9450a50783d6e58dcf3f39b0b680c45fdf4686e4bae653b75bf2d59840704:/app/main.py
```

run the script:

```bash
docker exec -it 15c9450a50783d6e58dcf3f39b0b680c45fdf4686e4bae653b75bf2d59840704 python3 /app/main.py
```

## Run the chatbot UI locally

First you have to change the `.env` file to point to localhost instead of host.docker.internal

Then run the following command: Shell:

```bash
chainlit run src/frontend/frontend/multimodal_chatbot.py --port 9999
```

Powershell:

```bash
chainlit run .\src\frontend\frontend\multimodal_chatbot.py --port 9999
```
