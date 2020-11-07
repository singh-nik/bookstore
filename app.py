import os , requests

#importing some additional packages and libraries
from flask import Flask ,url_for, render_template,request,session , redirect , jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#creating a flask app
app=Flask(__name__)

#configuring the session for the log in and log out purpose
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


#setting the path of the database 
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

api_key = "1lfRZuhkj9QCM92caQZQ"
#home page of the website 
@app.route("/")
def home():

    #if user is loged in than forward them to the find page 
    if session.get("login") is True:
        return redirect(url_for("login"))
    
    # if user is not login or for the new user 
    return render_template("home.html")

# to register a new user 
@app.route("/register" ,  methods=["POST"])
def register():

    # extracting the data entered in the form 
    username = request.form.get("username")
    password = request.form.get("password")
    repassword = request.form.get("repassword")

    if username=="" or password==""  or repassword =="":
        return render_template("ok.html" ,  message="Please enter all fields" )
    
    if(password == repassword):
        db.execute("insert into users (username , password) values(lower(:username) , :password)", {"username":username , "password":password})
        db.commit()
        return render_template("ok.html", message="Succesfully register , now please login " )
    
    else:
       return render_template("ok.html" , message="Please enter same password in both place")



# if user exist than give permission to them and login them
@app.route("/login" , methods=["POST","GET"])
def login():
    
    # if the user access here because of the get method or user is logged in than forward them to the find page 
    if request.method =="GET":
        return render_template ("find1.html" , username=session["user"])

    #extract information from the entred login data by the user
    username = request.form.get("username")
    password = request.form.get("password")

    #check wheather a user exist or not 
    user = db.execute("select * from users where username =lower(:username) and password =(:password) ",{"username":username , "password":password}).fetchone()
    if user is None:
        return render_template ("ok.html" , message="Please enter a valid username and password ")
    
    #make user loged in
    session["login"] = True
    session["user"] = user.username.lower()
    return render_template("find1.html" , username=username.lower() )
     

# search for a particular book
@app.route("/find" , methods=["GET"])
def find():

    #extract data from the choice entred by the user
    name = request.args.get("name")
    choice = request.args.get("choice")

    if choice is None:
        return render_template("ok.html" , message="Please select the  criteria of searching")
     
    # apply % character to both end of the string which is entred by the user 
    search="%"
    search = search + name + "%"

    #fetching database on the basis of the given choices by the user 
    if choice == "title":
        book = db.execute("SELECT * FROM books  WHERE LOWER(title) LIKE LOWER(:search)",{"search":search}).fetchall()     
    if choice == "isbn":
        book = db.execute("SELECT * FROM books  WHERE LOWER(isbn) LIKE LOWER(:search)",{"search":search}).fetchall()   
    if choice == "author":
        book = db.execute("SELECT * FROM books  WHERE LOWER(author) LIKE LOWER(:search)",{"search":search}).fetchall()   
    
    username = session["user"]

    return render_template("search.html" , book=book ,username=username )

# if user want to log out from the particular machine than terminate his/her session
@app.route("/logout")
def logout():

    session["login"]=False
    session["user"]="-"
    return render_template("home.html")

# find detail of  a particular book by the help of there isbn no.
@app.route("/book/<string:isbn>", methods=["POST", "GET"])
def book_detail(isbn):
    
    # check if user wants to submit the review by a post method 
    if request.method == "POST":

        #check wheather the user is loged in or not 
        if session.get("login") == False or session.get("login") == None :
            return render_template("ok.html" , message="Please login first than try to submit a review")
        
        # get the review and ratting given by the user and get the user name by the help of session
        name = session["user"]
        remark = request.form.get("remark")
        points = request.form.get("points")

        # check the charracter in the review is atleast 5 or not 
        if len(remark)<3 :
            return render_template("ok.html" , message="Please provide review minimum five charracter")
        elif int(points)<1 or int(points) >5 :
            return render_template("ok.html" , message="Please provide ratting between 1.00 to 5.00")
        
        # fetch information from database is user previously  submited a review for the given book
        check = db.execute("SELECT * FROM review WHERE username = (:username) AND isbn =(:isbn)",{"username":name ,"isbn":isbn}).fetchall()
        
        # if review existed previosly than delete the existing review
        if check != None:
            db.execute("DELETE FROM review WHERE  username = (:username) AND isbn =(:isbn)",{"username":name ,"isbn":isbn})
            db.commit()
        
        #insert the review and ratting given by the user into database 
        db.execute("INSERT INTO review(username, isbn , remark , points) values(:name,:isbn,:remark ,:points)",{"name":name , "isbn":isbn , "remark":remark , "points":points})
        db.commit()

    # getting data from goodreads API 
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": api_key, "isbns": isbn})
    result = res.json()
    
    # fetch the information of the book of the given isbn no.
    book = db.execute("SELECT * FROM books WHERE isbn =(:isbn)",{"isbn":isbn}).fetchone()
   
    # getting information from the json file
    review = float(result["books"][0]["average_rating"])
    gr_user_no = result["books"][0]["work_ratings_count"]
    
    # getting reviews by the users
    local_user = db.execute("SELECT * FROM review WHERE isbn = (:isbn )", {"isbn":isbn})
    count =  local_user.rowcount
    local_user = local_user.fetchall()
    
    # summing up the all the review and try to find average ratting
    internal_ratting = 0
    if count != 0:
        for i in local_user:
            internal_ratting = internal_ratting + i.points
        internal_ratting /= count
        internal_ratting =round(internal_ratting , 2)
    username = session["user"]

    return render_template("info.html",username=username , book=book ,review=review,gr_user_no=gr_user_no, internal_ratting=internal_ratting , count= count , local_user=local_user)
 


@app.route("/api/<string:isbn>")
def api( isbn ):
    book = db.execute("SELECT * FROM books WHERE isbn=(:isbn)",{"isbn":isbn}).fetchone()
    if book is None:
        return jsonify({"error":"Sorry,book not exist"}),404


    local_user = db.execute("SELECT * FROM review WHERE isbn = (:isbn )", {"isbn":isbn})
    count =  local_user.rowcount
    local_user = local_user.fetchall()
    
    # summing up the all the review and try to find average ratting
    internal_ratting = 0
    if count != 0:
        for i in local_user:
            internal_ratting = internal_ratting + i.points
        internal_ratting /= count
        internal_ratting = round(internal_ratting , 2)
        internal_ratting=str(internal_ratting)

    return jsonify({
        "title":book.title,
        "author":book.author,
        "year":book.year,
        "isbn":book.isbn,
        "review_count":count,
        "average_score":internal_ratting
    })

@app.route("/api")
def api_page():
    return render_template("api.html")
