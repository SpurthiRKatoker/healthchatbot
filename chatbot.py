from responder import Responder

class HealthChatbot:
    def __init__(self):
        self.responder = Responder()

    def get_response(self, user_input):
        return self.responder.get_response(user_input)


# Test the chatbot
if __name__ == "__main__":
    bot = HealthChatbot()
    print("🩺 Health Chatbot is ready! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Chatbot: Goodbye!")
            break
        response = bot.get_response(user_input)
        print("Chatbot:", response)
