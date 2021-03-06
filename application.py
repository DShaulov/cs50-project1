import os

from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import generate_password_hash, check_password_hash
from helpers import capitalizeAll, grRequest


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
            return redirect("/")
        else:
            message = "*username already taken"
            return render_template("register.html", message=message)

@app.route("/")
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        if session == {}:
            sessionCheck = session
            return render_template("login.html", sessionCheck=sessionCheck)
        else:
            return redirect("/search")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        userCheck = db.execute("SELECT * FROM users WHERE username=:username", {"username": username}).fetchall()
        print(userCheck)
        if userCheck == []:
            errormessage = "*username or password dont match"
            return render_template("login.html", errormessage=errormessage)

        if not check_password_hash(userCheck[0][2], password):
            errormessage = "*username or password dont match"
            return render_template("login.html", errormessage=errormessage)

        userId = userCheck[0][0]
        session["user_id"] = userId
        print(session["user_id"])
        return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "GET":
        return render_template("search.html")

    if request.method == "POST":
        searchParam = request.form.get("search")
        searchParam = capitalizeAll(searchParam)
        dbQuery = db.execute("SELECT title,author FROM books WHERE title LIKE :searchParam OR author LIKE :searchParam OR isbn LIKE :searchParam",
                            {"searchParam": "%"+searchParam+"%"}).fetchall()
        print(dbQuery)
        return render_template("search.html", dbQuery=dbQuery)

@app.route("/books/<string:book>", methods=['GET'])
def books(book):
    if request.method == "GET":
        bookName = book
        details = db.execute("SELECT * FROM books WHERE title = :title", {"title": bookName}).fetchall()
        isbn = db.execute("SELECT isbn FROM books WHERE title = :title", {"title": bookName}).fetchall()
        reviews = db.execute("SELECT username,review,rating FROM users INNER JOIN review ON users.id = review.id WHERE isbn= :isbn",
                            {"isbn": isbn[0][0]}).fetchall()
        print(reviews)
        ratings = grRequest(isbn[0][0])
        print(ratings)
        return render_template("books.html", details=details, ratings=ratings, reviews=reviews)

@app.route("/review", methods=["POST", "GET"])
def review():
    if request.method == "GET":
        return render_template("review.html")

    if request.method == "POST":
        db.execute("INSERT INTO review (id, review, rating, isbn) VALUES (:ids, :review, :rating, :isbn)",
                    {"ids": session["user_id"], "review": request.form.get("review"), "rating": request.form.get("rating"),
                    "isbn": request.form.get("isbn")})
        db.commit()
        thankyou = "Thank you for submitting a review"
        return render_template("search.html", thankyou=thankyou)

@app.route("/reviewpost", methods=["POST"])
def reviewPost():
    isbn = request.form.get("isbn")
    print(isbn)
    userReviews = db.execute("SELECT username,review,rating FROM users INNER JOIN review ON users.id = review.id WHERE isbn= :isbn AND users.id= :ids",
                            {"isbn": isbn, "ids": session['user_id']}).fetchall()
    print(userReviews)

    if userReviews != []:
        title = request.form.get("title")
        bookName = title
        details = db.execute("SELECT * FROM books WHERE title = :title", {"title": bookName}).fetchall()
        isbn = db.execute("SELECT isbn FROM books WHERE title = :title", {"title": bookName}).fetchall()
        reviews = db.execute("SELECT username,review,rating FROM users INNER JOIN review ON users.id = review.id WHERE isbn= :isbn",
                            {"isbn": isbn[0][0]}).fetchall()
        ratings = grRequest(isbn[0][0])
        errorMulti = "*you already reviewed this book"
        return render_template("books.html", details=details, ratings=ratings, reviews=reviews, errorMulti=errorMulti)
        



    return render_template("review.html", isbn=isbn)


@app.route("/api/<string:isbn>")
def apiRequest(isbn):

    # Check that book exists
    bookCheck = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    if bookCheck == []:
        return 404
    ratings = grRequest(isbn)
    response = {
        "title": bookCheck[0][1],
        "author": bookCheck[0][2],
        "publication date": bookCheck[0][3],
        "ISBN number": bookCheck[0][0],
        "review count": ratings[0],
        "average score": ratings[1]
    }
    return jsonify(response)

@app.route("/api")
def api():
    return render_template("api.html")