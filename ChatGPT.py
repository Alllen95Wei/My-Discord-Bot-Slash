from revChatGPT.V1 import Chatbot
from OpenAIAuth import Auth0
from dotenv import load_dotenv
from os import getenv

load_dotenv("TOKEN.env")
auth = Auth0(email=str(getenv("email")), password=str(getenv("password")))
access_token = auth.get_access_token()
chatbot = Chatbot(config={"access_token": access_token})


def chat(msg: str):
    prev_text = ""
    start_response = True
    for data in chatbot.ask(
            msg + "\n請用繁體中文回答。"
    ):
        if start_response:
            print("Bot: ", end="")
            start_response = False
        message = data["message"][len(prev_text):]
        print(message, end="", flush=True)
        prev_text = data["message"]
    return prev_text
