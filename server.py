from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """
    Starts the Flask server in a separate thread.
    Useful for keeping the bot alive on services like Replit.
    """
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    # If run directly, start the server
    run()
