from flask import Flask, render_template
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config[
    "MONGO_URI"
] = ""
mongo = PyMongo(app)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/register", methods=["POST"])
def register():
    return


@app.route("/login", methods=["POST"])
def login():
    return


if __name__ == "__main__":
    app.run(debug=True)