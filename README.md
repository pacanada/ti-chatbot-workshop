# ti-chatbot-workshop
Repository used for the T&amp;I conference: **Smart Chatbot Workshop**

## Run application

0. Be in the office or connect with a VPN to DFDS network
1. Copy the `.env.example` file to `.env` and fill in the required values
2. Setup: Run `docker-compose up --build part_1`:
    - Exercise 0: Check UI in localhost:8080 and ask any question related to Poland
    - Exercise 1: Include your own files in `part_1/txt_data/` to be used for RAG
    - Exercise 2: Add a welcome message: `part_1/frontend.py`
    - Exercise 3: Modify assistant system message in: `part_1/chatbot.py`
    - Exercise 4: Adjust number of retrieved documents in `part_1/chatbot.py`
3. Multimodal:
    - ...

