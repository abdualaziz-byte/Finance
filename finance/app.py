import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
            id = session["user_id"]

            balance = db.execute("SELECT cash FROM users WHERE  id = ?",id)[0]["cash"]

            funds = float(request.form.get("addfunds"))
            db.execute("UPDATE users SET cash = ? WHERE id = ? ",balance+funds,id)
            return redirect("/history")


    if request.method == "GET":

       id = session["user_id"]
       balance = db.execute("SELECT cash FROM users WHERE  id = ?",id)[0]["cash"]
       portfolio = db.execute("SELECT symbol, SUM(shares) AS shares FROM portfolio WHERE user_id = ? GROUP BY symbol",id)

       for x in portfolio:

         x["price"] = lookup(x["symbol"])["price"]



       return   render_template("index.html",balance= balance, portfolio= portfolio)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
     if request.method == "GET":
       return  render_template("buy.html")
     if request.method == "POST":
             if not request.form.get("symbol"):
                         return apology("must provide name of symbol", 403)


             elif not request.form.get("amount"):
              return apology("must provide amount of shares to buy", 403)
             if  int(request.form.get("amount")) <1 :
              return apology("must provide amount of shares higher or equal  to 1 ", 402)

             if  not lookup(request.form.get("symbol")):
                                                           return apology("stock doesnt exist", 398)
             id = session["user_id"]
             balance = db.execute(" SELECT cash FROM users WHERE id = ?",id)[0]["cash"]
             priceOstock =     lookup(request.form.get("symbol"))["price"]
             amountOstocks =  int(request.form.get("amount"))
             stockstotal = (priceOstock* amountOstocks)
             newbalance = balance -    stockstotal
             time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
             if     newbalance < 0 :
                     return apology(" not enough  funds ",397)
             else :
                     db.execute("UPDATE users SET cash =? WHERE id =?",newbalance,id)
                     db.execute("INSERT INTO portfolio (user_id, symbol, shares,price,date,transaction_type) VALUES (?,?,?,?,?,?)",id,request.form.get("symbol").upper(),amountOstocks,stockstotal,time,"BUY")

     return redirect("/buy")













@app.route("/history", methods=["GET", "POST"])
@login_required
def history():



  if request.method == "GET":

    id = session["user_id"]


    history = db.execute("SELECT * FROM portfolio WHERE user_id = ?", id)

    return render_template("history.html",history=history)




@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
       return  render_template("quote.html")
    elif request.method == "POST":
              if not request.form.get("symbol"):
                             return apology("must provide symbol", 403)
              symbol = lookup(request.form.get("symbol"))
              if not symbol :
                                                  return apology("symbol does not exist", 401)
              else: return render_template("stock.html",name = symbol["name"],price = symbol["price"],symbol = symbol["symbol"])








@app.route("/register", methods=["GET", "POST"])
def register():
  """Register user"""
  if request.method == "GET":
   return  render_template("register.html")
  if request.method == "POST":
        if not request.form.get("username"):
                   return apology("must provide username", 403)
        elif not request.form.get("password"):
                    return apology("must provide password", 403)
        elif not request.form.get("conformation"):
                            return apology("must provide password", 403)
        elif  request.form.get("conformation")  != request.form.get("password"):
                                    return apology("Password Doesnt match password conformation", 403)
        rows = db.execute( "SELECT * FROM users WHERE username = ?", request.form.get("username") )

        try :
              db.execute( "INSERT INTO users (username, hash) VALUES (?,?)",request.form.get("username"),generate_password_hash(request.form.get("password")))
              rows = db.execute("SELECT id FROM users WHERE username = ?",request.form.get("username"))
              session["user_id"] = rows[0]["id"]
              return redirect("/")

        except  ValueError: return apology("Username is already taken")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
           return  render_template("sell.html")

    if request.method == "POST":
             if not request.form.get("symbol"):
                         return apology("must provide name of symbol", 403)


             elif not request.form.get("amount"):
              return apology("must provide amount of shares to sell", 403)
             if  int(request.form.get("amount")) <1 :
              return apology("must provide amount of shares higher or equal  to 1 ", 402)

             if  not lookup(request.form.get("symbol")):
                                                           return apology("stock doesnt exist", 398)

             id = session["user_id"]
             balance = db.execute(" SELECT cash FROM users WHERE id = ? ",id)[0]["cash"]
             priceOstock =     lookup(request.form.get("symbol"))["price"]
             amountOstocks =  int(request.form.get("amount"))
             stockstotal = (priceOstock* amountOstocks)
             newbalance = balance +   stockstotal
             stockswantedtosell = db.execute("SELECT SUM(shares) AS shares  FROM portfolio WHERE user_id = ? AND symbol = ?",id,request.form.get("symbol").upper())[0]["shares"]
             time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
             if     stockswantedtosell < amountOstocks :
                     return apology(" not enough  stocks ",390)
             else :
                     db.execute("UPDATE users SET cash =? WHERE id =?",newbalance,id)
                     db.execute("INSERT INTO portfolio (user_id, symbol, shares,price,date,transaction_type) VALUES (?,?,?,?,?,?)",id,request.form.get("symbol").upper(),-amountOstocks,stockstotal,time,"SELL")

    return redirect("/sell")
