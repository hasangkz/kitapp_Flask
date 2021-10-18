from MySQLdb import cursors
from flask import Flask,render_template,redirect,url_for,session,logging,request,flash
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField, form,validators
from passlib.hash import sha256_crypt
from wtforms.validators import DataRequired, Length, Email, EqualTo
from functools import wraps

app=Flask(__name__)
app.secret_key = "kitapp"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "kitapp"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

# DECARETOR

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if "log" in session:
            return f(*args, **kwargs)
        
        else:
            flash("Please login to view this page!","danger")
            return redirect(url_for("login"))
    return decorated_function

# KİTAP GÜNCELLE

@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def edit(id):
    
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        q6="Select * from books where id = %s and author = %s "
        result=cursor.execute(q6,(id,session["username"]))
        if result == 0:
            flash("No such book exists or you are not authorized to","danger")
            return redirect(url_for("signin"))
        else:
            staff = cursor.fetchone()
            form =  BookForm()
            form.title.data = staff["title"]
            form.content.data = staff["content"]
            return render_template("update.html",form=form)
    else:
        form = BookForm(request.form)
        new_Title = form.title.data
        new_Content = form.content.data

        q7 = "Update books Set title = %s,content = %s where id = %s"
        
        cursor = mysql.connection.cursor()

        cursor.execute(q7,(new_Title,new_Content,id))

        mysql.connection.commit()
        flash("Update is worked","success")
        return redirect(url_for("dashboard"))





# KİTAP SİL

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    q5 = "Select * from books where author = %s and id = %s "

    result = cursor.execute(q5,(session["username"],id))

    if result > 0:
        r6 = "Delete from books where id = %s"
        cursor.execute(r6,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("No such book exists or you are not authorized to","danger")
        return redirect(url_for("signin"))



# DETAY KİTAP

@app.route("/book/<string:id>")
@login_required
def detay(id):
    cursor = mysql.connection.cursor()
    q4 = "Select * From books where id = %s"
    result = cursor.execute(q4,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")
    

# Kullanıcı kayıt formu oluşturuyoruz, WTF ile

class RegisterForm(Form):
    name = StringField("Name and Surname",validators = [validators.DataRequired(message = "Please enter the name and surname"),validators.Length(min=5,max=25)])
    username = StringField("Username",validators=[validators.DataRequired(message= "Please enter the username"),validators.Length(min=3,max=19)])
    mail = StringField("Email",validators=[validators.DataRequired(message="Please enter the mail"),validators.Email(message="Enter a valid mail")])
    password = PasswordField("Password",validators=[

        validators.DataRequired(message="Please enter the password"),
        validators.equal_to(fieldname="confirm",message="Passwords do not match, Please try again")

    ])

    confirm = PasswordField("Verify Password",validators=[validators.DataRequired(message="Enter the password")])

#Kullanıcı Paneli
@app.route("/dashboard")
@login_required

def dashboard():

    cursor = mysql.connection.cursor()

    q3 = "Select * From books where author = %s"

    result = cursor.execute(q3,(session["username"],))

    if result > 0:
        book = cursor.fetchall()
        return render_template("dashboard.html",book=book)
    else:
        return render_template("dashboard.html")



# Yeni Kayıt
@app.route("/register",methods = ["GET","POST"])

def register():

    form = RegisterForm(request.form)

    if request.method=="POST" and form.validate():
        name = form.name.data
        username = form.username.data
        mail = form.mail.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        q="Insert into users(name,username,mail,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(q,(name,username,mail,password))

        mysql.connection.commit()

        cursor.close()

        flash("You have successfully registered!","success")

        return redirect(url_for("login"))

    else:
        return render_template("register.html",form = form)


class LoginForm(Form):

    username = StringField("Username")
    password = PasswordField("Password")


# Giriş Yap
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)

    if request.method=="POST" and form.validate():
        username = form.username.data
        password_e = form.password.data

        cursor = mysql.connection.cursor() 

        q1 = "Select * From users where username = %s"

        result = cursor.execute(q1,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_e,real_password):

                flash("Login successful! {} ".format(username),"success")

                session["log"] = True
                session["username"] = username

                return redirect(url_for("signin"))

            else:
                flash("Login failed! Wrong password","danger")


                return redirect(url_for("login"))


        else:
            flash("There is no such user","danger")
            return redirect(url_for("login"))

    

    return render_template("login.html",form = form)

# Çıkış Yap
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))

# Ana Sayfa
@app.route("/")
def signin():
    numbers=[24.99,29.99,34.99]

    books=[

        {"id":11284459,"title":"Peter Pan","cont":"adventure"},
        {"id":11284757,"title":"Le Petit Prence","cont":"adventure"},
        {"id":11285926,"title":"Hong lou meng","cont":"epic"}

    ]

    return render_template("ornek2.html",order="yes",numbers=numbers,books=books)


# Kitaplar
@app.route("/books")
@login_required
def books():
    cursor = mysql.connection.cursor()
    q2 = "Select * From books"

    result = cursor.execute(q2)
    if result > 0:
        data = cursor.fetchall()
        return render_template("books.html",data=data)
    else:
        return render_template("books.html")


# Arama
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("signin"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        q8 = "Select * from books where title like '%" + keyword + "%' "
        result = cursor.execute(q8) 

        if result > 0:
            bookss = cursor.fetchall()
            return render_template("books.html",data=bookss)

        else:
            flash("Unfortunately there is no such book!","warning")
            return redirect(url_for("books"))



# IDye göre kitap arama
@app.route("/books/<string:id>")
def detail(id):
    if id.isnumeric() == True:
        return "Book ID " + id
    else:
        return "A false ID, Please try again!"

# Biz Kimiz
@app.route("/who-are-we")
def whoarewe():
    return render_template("whoarewe.html")

# Kitap Form
class BookForm(Form):
    title = StringField("Title",validators=[validators.DataRequired(message = "Please enter the title of the book"),validators.Length(min = 3,max = 55)])
    content = TextAreaField("Summary of Book",validators=[validators.DataRequired(message = "Please enter the sumamry of the book"),validators.Length(min = 20)])


# Kitap Ekleme
@app.route("/addbook",methods=["GET","POST"])
@login_required
def addbok():
    form = BookForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data


        cursor = mysql.connection.cursor()


        q2="Insert  into books(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(q2,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Book successfully added","succes")

        return redirect(url_for("dashboard"))

    return render_template("addbook.html",form=form)




if __name__ == "__main__":
    app.run(debug=True)