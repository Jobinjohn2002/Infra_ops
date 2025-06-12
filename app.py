from flask import Flask, render_template_string
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'flaskuser'
app.config['MYSQL_PASSWORD'] = 'Excel@123'
app.config['MYSQL_DB'] = 'flaskdb'

mysql = MySQL(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users")
    data = cur.fetchall()
    cur.close()

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Users List</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h2 class="mb-0">Users List in Table view</h2>
                </div>
                <div class="card-body">
                    {% if users %}
                        <ul class="list-group">
                            {% for user in users %}
                                <li class="list-group-item">
                                    <strong>ID:</strong> {{ user[0] }} |
                                    <strong>Name:</strong> {{ user[1] }}
                                </li>
                            {% endfor %}
                        </ul>
                    {% else %}
                        <p class="text-muted">No users found in the database.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, users=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
