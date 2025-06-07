from flask import Flask
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Hello from Flask on Azure VM! This is for testing. Triggering worked successfully!."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
