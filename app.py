from flask import Flask
import threading
import time

app = Flask(__name__)

def cpu_intensive_task():
    # This will run an infinite loop to simulate CPU usage
    while True:
        _ = 0
        for i in range(10**6):
            _ += i

# Start the CPU intensive task in a background thread
threading.Thread(target=cpu_intensive_task, daemon=True).start()

@app.route('/', methods=['GET'])
def home():
    return "Hello from Flask on Azure VM! This is for testing. CPU load should trigger alert soon."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
