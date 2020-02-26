import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)


os.environ["DATABASE_URL"] = "postgres://xgqjlgqhllptkx:b0c038bec42ebc57dc2b89fb87447625e20ffd4e7eb5e2589831e7910ae84258@ec2-54-247-125-38.eu-west-1.compute.amazonaws.com:5432/d88oobt5q6ppat"
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("frontpage.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        username = request.form.get("username")
        usercheck = db.execute("SELECT * FROM USERS WHERE USERNAME= :USERNAME", {"USERNAME":username}).fetchall()
        if usercheck == []:
            x = request.form.get("password")
            hashedPass = generate_password_hash(request.form.get("password"))
            db.execute("INSERT INTO USERS (USERNAME, HASH) VALUES (:USERNAME, :HASH)", {"USERNAME": username, "HASH": hashedPass})
            db.commit()
        else:
            message = "*username already taken"
            return render_template("register.html")
        return "Cool it posted!"
