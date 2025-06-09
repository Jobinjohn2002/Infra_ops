from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask on Azure VM</title>
        <style>
            body {
                background-color: #f0f8ff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            h1 {
                color: #0078d7;
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
            p {
                font-size: 1.2rem;
                color: #333;
            }
        </style>
    </head>
    <body>
        <h1>Hello from Flask on Azure VM!</h1>
        <p>This is for testing. Triggering worked successfully from VS Code!</p>
        <p>This page is for testing</p>
    </body>
    </html>
    """
    return render_template_string(html_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
