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
    <h2>User List</h2>
    <ul>
    {% for user in users %}
        <li>ID: {{ user[0] }}, Name: {{ user[1] }}</li>
    {% endfor %}
    </ul>
    """
    return render_template_string(html, users=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
