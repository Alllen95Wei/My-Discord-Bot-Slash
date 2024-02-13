# from revChatGPT.V1 import Chatbot
# from OpenAIAuth import Auth0
# from dotenv import load_dotenv
# from os import getenv
#
#
# class ChatBot:
#     def __init__(self):
#         load_dotenv("TOKEN.env")
#         auth = Auth0(email_address=str(getenv("email")), password=str(getenv("password")))
#         access_token = auth.get_access_token()
#         self.chatbot = Chatbot(config={"access_token": access_token})
#
#     def chat(self, msg: str):
#         prev_text = ""
#         start_response = True
#         for data in self.chatbot.ask(msg):
#             if start_response:
#                 print("Bot: ", end="")
#                 start_response = False
#             responded_message = data["message"][len(prev_text):]
#             print(responded_message, end="", flush=True)
#             prev_text = data["message"]
#         return prev_text
#
#
# if __name__ == "__main__":
#     bot = ChatBot()
#     while True:
#         message = input("You: ")
#         bot.chat(message)
#         print()
