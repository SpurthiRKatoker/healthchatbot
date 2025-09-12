import joblib
import json
import os

# Paths
MODEL_PATH = "model.pkl"
RESPONSES_PATH = os.path.join("data", "responses.json")

class Responder:
    def __init__(self):
        # Load trained model
        self.model = joblib.load(MODEL_PATH)

        # Load responses
        with open(RESPONSES_PATH, "r") as file:
            self.responses = json.load(file)

    def get_response(self, user_input):
        # Predict intent
        intent = self.model.predict([user_input])[0]

        # Get response text
        response = self.responses.get(intent, "Sorry, I don't understand that.")

        return response

if __name__ == "__main__":
    bot = Responder()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Chatbot: Goodbye!")
            break
        reply = bot.get_response(user_input)
        print("Chatbot:", reply)
