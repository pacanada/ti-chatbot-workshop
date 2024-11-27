import logging

import chainlit as cl

from chatbot import Chatbot

chatbot = Chatbot()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@cl.on_message
async def main(message: cl.Message) -> None:
    # Ensure user session has a history object
    if not hasattr(cl.user_session, "history"):
        cl.user_session.set("history", [])
    history = cl.user_session.get("history")

    # Add the user's message to the history and trim it
    history.append(message.content)
    history = history[-3:]
    cl.user_session.set("history", history)

    # Get the chatbot's response
    knowledge_context, response = chatbot.chat("\n\n".join(history))

    # Log and display retrieved context
    logger.info(f"Retrieved Context: {chatbot._get_knowledge_context_str()}")

    # Use Chainlit's classes for displaying retrieved context
    elements = [
        cl.Text(name=doc_id, content=text, display="side")
        for doc_id, text in knowledge_context.items()
    ]

    # Send the response and elements back to the user
    await cl.Message(content=response, elements=elements).send()


# @cl.on_chat_start
# async def on_chat_start():
#     await cl.Message(content="Yarr, welcome to ye pirate assistant... ask away!").send()
