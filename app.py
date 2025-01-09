from flask import Flask,render_template,request,session,redirect,url_for
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from bson import ObjectId
from datetime import datetime
from bson.errors import InvalidId
import os

api=Flask(__name__)
api.secret_key="1234567890"

cluster=MongoClient("mongodb://127.0.0.1:17017")
db=cluster['KITS-SOC-Library']
uregister=db['uregister']
addbook=db['addbook']
borrowed=db['borrowed']
returnbook=db['returnbook']
requests=db['requests']


UPLOAD_FOLDER = 'static/uploads/'  # Set your desired folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api.route("/")
def index():
    return render_template("index.html")

@api.route("/ureg")
def ureg():
    return render_template("userregister.html")

@api.route("/ulog")
def ulog():
    return render_template("userlogin.html")

@api.route("/admlog")
def admlog():
    return render_template("adminlogin.html")

@api.route("/admindex")
def admindex():
    return render_template("adminindex.html")

@api.route("/admviewbooks")
def admviewbooks():
    return render_template("adminviewbooks.html")

@api.route("/userbrbooks")
def userbrbooks():
    return render_template("userborrowedbooks.html")

@api.route("/userindex")
def userindex():
    books=list(addbook.find())
    return render_template("userindex.html",books=books)

@api.route("/userviewd")
def userviewd():
    return render_template("userviewdetails.html")

@api.route("/adminlogin",methods=['post'])
def adminlog():
    admin_username = "admin"
    admin_password = "password1234"
    uname = request.form.get("username")
    upass = request.form.get("password")
    session['user']="admin"
    print(uname,upass)
    if uname == admin_username and upass == admin_password:
        return render_template("adminindex.html")
    return render_template("adminlogin.html",status="Invalid Credentials")

@api.route("/userregister",methods=['post'])
def userregister():
    uname=request.form.get("username")
    uemail=request.form.get("email")
    uphone=request.form.get("phone")
    upass=request.form.get("password")
    print(uname,uemail,uphone,upass)
    user = uregister.find_one({"username": uname})
    if user:
        return render_template("userregister.html",status="User Already Existed")
    uregister.insert_one({"username": uname,"email": uemail,"phone": uphone,"password": upass})
    return render_template("userregister.html",status1="Registration Successful")

@api.route("/userlogin",methods=['post'])
def userlogin():
    uname=request.form.get("username")
    upass=request.form.get("password")
    print(uname,upass)
    user=uregister.find_one({"username": uname})
    if user:
        if user["password"] == upass:
            session['username']=uname
            return redirect("/homepage")
       
        return render_template("userlogin.html",status="Invalid Login Credentials")
    
@api.route("/homepage")
def userlog():
    books=list(addbook.find())
    return render_template("userindex.html",books=books)

@api.route("/addbookdetail",methods=['post'])
def addbookdetail():
    title=request.form.get("title")
    author=request.form.get("author")
    publisher=request.form.get("publisher")
    year_published=request.form.get("year_published")
    isbn=request.form.get("isbn")
    cover_image=request.files.get("cover_image")
    description=request.form.get('description')
    number=request.form.get('number')

    print(title,author,publisher,year_published,isbn,cover_image)
    cover_image_path = None

    # If a file is uploaded and the file is allowed, save the file
    if cover_image and allowed_file(cover_image.filename):
        filename = secure_filename(cover_image.filename)
        cover_image_path = os.path.join(UPLOAD_FOLDER, filename)
        cover_image.save(cover_image_path) 
    addbook.insert_one({"title":title,"author":author,"publisher":publisher,"year_published":year_published,"isbn":isbn,"cover_image":cover_image_path,"borrowed_by":[],"number":number,"description":description})
    return render_template("adminindex.html",status="Book details added successfully")

@api.route("/viewbooks")  # This Api is for retreaving bookdetails from the db and display
def viewbooks():
    books=addbook.find()
    books=list(books)
    return render_template("adminviewbooks.html",books=books)

@api.route("/delete/<book_id>",methods=['get']) #To delete book
def deletebook(book_id):
    book_id=ObjectId(book_id)
    addbook.delete_one({"_id":book_id})

    books=addbook.find()
    books=list(books)

    return redirect("/viewbooks")

@api.route("/editbook/<book_id>") #This Api is for edit book details page redirection based on id
def editbook(book_id):
    book=addbook.find_one({"_id": ObjectId(book_id)})

    if book:
        return render_template("updateddetails.html",book=book)
    
@api.route("/updatebook/<book_id>", methods=["POST"])
def updatedbook(book_id):
    # Ensure book_id is converted to ObjectId
    book_id = ObjectId(book_id)
    
    # Retrieve form data
    title = request.form.get("title")
    author = request.form.get("author")
    publisher = request.form.get("publisher")
    year_published = request.form.get("year_published")
    isbn = request.form.get("isbn")
    cover_image = request.files.get("cover_image")
    description=request.form.get("description")
    number=request.form.get("number")

    # Define the document to update
    update_data = {
        "title": title,
        "author": author,
        "publisher": publisher,
        "year_published": year_published,
        "isbn": isbn,
        "description":description,
        "number":number
    }

    # Handle cover image upload if provided
    if cover_image:
        # Save the uploaded file to a desired location and get its path
        cover_image_path = f"static/uploads/{cover_image.filename}"
        cover_image.save(cover_image_path)
        update_data["cover_image"] = cover_image_path

    # Update the document in the database
    addbook.update_one({"_id": book_id}, {"$set": update_data})

    # Redirect or render a template after update (optional)
    return redirect("/viewbooks")

@api.route("/logout")
def home():
    return render_template("index.html")

@api.route("/viewbuttton/<book_id>")
def viewbutton(book_id):
    details = addbook.find_one({"_id": ObjectId(book_id)})
    return render_template("userviewdetails.html",book=details)

@api.route("/borrow/<book_id>")
def borrow_book(book_id):
    # Ensure the user is logged in
    if 'username' not in session:
        return render_template("userlogin.html", status="Please login to borrow")

    # Get the username from session
    username = session['username']

    try:
        # Fetch the book by its ObjectId
        book = addbook.find_one({"_id": ObjectId(book_id)})

        if not book:
            return render_template("userviewdetails.html", status="Book not found", book=None)

        # Check if the user has already borrowed the book
        print(username)
        if username in book.get("borrowed_by", []):
            return render_template("userviewdetails.html", status="You have already borrowed this book", book=book)

        # Check if the book is available to borrow
        if int(book["number"]) > 0:
            # Decrement the number of available books by 1
            addbook.update_one(
                {"_id": ObjectId(book_id)},
                {
                    "$push": {"borrowed_by": username},
                    "$set": {"number":str(int(book["number"])-1)}
                }
            )

            # Fetch the updated book details
            updated_book = addbook.find_one({"_id": ObjectId(book_id)})
            return render_template("userviewdetails.html", status="You have successfully borrowed the book", book=updated_book)
        else:
            return render_template("userviewdetails.html", status="Sorry, this book is currently not available", book=book)

    except InvalidId:
        return render_template("userviewdetails.html", status="Invalid book ID", book=None)
@api.route("/my_borrowed_books", methods=["GET"])
def my_borrowed_books():
    # Ensure the user is logged in
    if 'username' not in session:
        return render_template("userlogin",status="Please login to borrow")

    # Get the username from session
    username = session['username']

    # Fetch all books where the logged-in user has borrowed the book
    borrowed_books = addbook.find({"borrowed_by": username})

    # Convert the cursor to a list of books
    borrowed_books_list = list(borrowed_books)

    # If no books are found
    if not borrowed_books_list:
        return render_template("userborrowedbooks.html",status="No books borrowed")

    # Return the list of borrowed books
    books_data = []
    for book in borrowed_books_list:
        books_data.append({
            "title": book["title"],
            "author": book["author"],
            "publisher": book["publisher"],
            "_id": str(book["_id"])  # Convert ObjectId to string
        })

    return render_template("userborrowedbooks.html",borrowed_books=books_data)

@api.route("/return/<book_id>", methods=["GET", "POST"])
def return_book(book_id):
    # Check if the user is logged in (username exists in session)
    if 'username' not in session:
        return render_template("userlogin.html", status="Please login to return")  # Redirect to login page if not logged in
    
    username = session['username']  # Retrieve username from session
    
    # Check if the username already borrowed this book
    book = addbook.find_one({"_id": ObjectId(book_id), "borrowed_by": username})

    if not book:
        # If the book is not found in the borrowed_by array, return error message
        print("User has not borrowed this book")
        return render_template("userborrowedbooks.html", status="You have not borrowed this book", return_id=book_id)
    
    if request.method == "POST":
        book = addbook.find_one({"_id": ObjectId(book_id)})  # Get book from the database

        # If the book is not found, re-render the page with an error message
        if not book:
            print("Book not found")
            return render_template('userborrowedbooks.html', error="Book not found", return_id=book_id)

        # Prepare data for return request
        return_data = {
            "username": username,
            "bookname": book['title'],  # Get book title from the fetched book
            "book_id": book_id
        }

        # Insert the return request into the MongoDB collection
        returnbook.insert_one(return_data)

        # Remove the username from the borrowed_by array and increment the book number
        addbook.update_one(
            {"_id": ObjectId(book_id)},
            {
                "$pull": {"borrowed_by": username},  # Remove username from borrowed_by array
                "$set": {"number": str(int(book["number"]) + 1)}  # Increment the available number of books
            }
        )

        # Redirect to the borrowed books page after returning the book
        return redirect("/my_borrowed_books")

    return render_template("userborrowedbooks.html", return_id=book_id)

@api.route("/returnaccept")
def returnaccept():
    books=list(returnbook.find())
    print(books)
    return render_template("adminaceept.html",books=books)

@api.route("/acceptreturn")
def acceptreturn():
    id=request.args.get("id")
    data=returnbook.find_one({"_id":ObjectId(id)})
    print(data)
    returnbook.delete_one({"_id":ObjectId(id)})
    addbook.update_one({"_id":data["bookname"]["_id"]},{"$pull":{"borrowed_by":data['username']}})
    return redirect("/returnaccept")

@api.route("/requestbook/<book_id>")
def requestbook(book_id):
    book=addbook.find_one({"_id":ObjectId(book_id)})
    request_entry = {
            "title": book['title'], # Get from form input
            "book_id":book_id,
            "author":book['author'],
            "publisher":book['publisher'],
            "status":"pending",
            "requested_by": session['username']  # Get user info from form input
    }
    requests.insert_one(request_entry)
    details = addbook.find_one({"_id": ObjectId(book_id)})
    return render_template("userviewdetails.html",book=details,status="Book request sent successfully")
    
@api.route("/userbookrequests")
def userbookrequests():
    user_requests=requests.find({"requested_by":session['username']})
    return render_template("userrequests.html",requests=user_requests)

@api.route("/updaterequeststatus/<request_id>", methods=["POST"])
def update_request_status(request_id):
    try:
        # Ensure request_id is a valid ObjectId
        valid_request_id = ObjectId(request_id)
        
        # Update the status of the request to "book available"
        result = requests.update_one(
            {"_id": valid_request_id},
            {"$set": {"status": "Book available"}}
        )
        
        if result.matched_count > 0:
            # Redirect to a page showing all requests or a success message
            return redirect("/adminrequests")  # Replace with appropriate view function
        else:
            return render_template("error.html", message="Request not found or already updated.")
    
    except InvalidId:
        # Handle the error if the ObjectId is invalid
        return render_template("error.html", message="Invalid request ID.")
    
@api.route("/deleterequest/<request_id>", methods=["POST"])
def delete_request(request_id):
    try:
        # Ensure request_id is a valid ObjectId
        valid_request_id = ObjectId(request_id)
        
        # Delete the request document from the database
        result = requests.delete_one({"_id": valid_request_id})
        
        if result.deleted_count > 0:
            # Redirect to a page showing all requests or a success message
            return redirect("/adminrequests")  # Replace with appropriate view function
        else:
            return render_template("error.html", message="Request not found or already deleted.")
    
    except InvalidId:
        # Handle the error if the ObjectId is invalid
        return render_template("error.html", message="Invalid request ID.")

@api.route("/userdeleterequest/<request_id>", methods=["POST"])
def delete_request_user(request_id):
    try:
        # Ensure request_id is a valid ObjectId
        valid_request_id = ObjectId(request_id)
        
        # Delete the request document from the database
        result = requests.delete_one({"_id": valid_request_id})
        
        if result.deleted_count > 0:
            # Redirect to a page showing all requests or a success message
            return redirect("/userbookrequests")  # Replace with appropriate view function
        else:
            return render_template("error.html", message="Request not found or already deleted.")
    
    except InvalidId:
        # Handle the error if the ObjectId is invalid
        return render_template("error.html", message="Invalid request ID.")
    
  
@api.route("/adminrequests")
def adminrequests():
    book_requests=requests.find({"status":"pending"})
    return render_template('adminrequests.html',requests=book_requests)

    
if __name__=="__main__":
    api.run(host='0.0.0.0', port=6021,debug=True)
