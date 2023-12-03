import json
import time
import random
import string
from flask import Flask, render_template, request, session, redirect

UPLOAD_FOLDER = "uploads"

app = Flask(__name__, template_folder="site")
app.secret_key = "YardaX64"
symbols = "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm0123456789_"

class User:
    def __init__(self, file):
        self.file = file   

    def set_user(self, username, password):     

        with open("database/accounts.json", "r") as file:
            users = json.load(file)

        if username not in users.keys():
            users[username] = {"password": password, "followers": [], "description": "Я пользователь Yarda!"}
        else:
            return "user is registered"
        
        with open("database/accounts.json", "w") as file:
            json.dump(users, file)
        
    def validate_username(self, username):
        return all(char.upper() in symbols for char in username)

with open("database/settings.json", "r") as file:
    config = json.load(file)

with open("database/moderators.json") as file:
    moderators = json.load(file)

messages = []
users = []
posts = []

@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500

@app.errorhandler(404)
def server_error(error):
    return render_template("errors/404.html"), 404

@app.route("/")
def main():
    return render_template("index.html")

@app.route("/index")
def index():
    return render_template("main_page.html", posts=posts)

@app.route("/register")
def reg():
    return render_template("register.html")

@app.route("/api")
def api():
    return render_template("api.html")

@app.route("/api/posts")
def all_posts():
    return {"result": len(posts)}

@app.route("/api/getPost")
def get_post_content():
    post = int(request.args.get("post_id"))
    try:
        return {"result": posts[post]}
    except: 
        return {"result": "error"}
    
@app.route("/api/getUserFollowers")
def get_user_followers():

    username = request.args.get("username")
    content_datatype = request.args.get("int")

    with open("database/accounts.json", "r") as file:
        data = json.load(file)

    if (username not in data): return {"result": "error"}

    if (content_datatype == "true"): 
        return {"result": len(data[username]["followers"])}
    
    elif (content_datatype == "false"): 
        return {"result": data[username]["followers"]}
    
    else: 
        return {"result": "error"}
    
@app.route("/api/getUserDescription")
def get_description():
    username = request.args.get("username")

    with open("database/accounts.json", "r") as file:
        users = json.load(file)

    try:
        return {"result": users[username]["description"]}
    except:
        return {"result": "error"}

@app.route("/register_", methods=["POST"])
def reg2():

    with open("database/accounts.json", "r") as file:
        content = json.load(file)

    account_name = request.args.get("username")

    username = request.form["username"]

    if (not User("site").validate_username(username)):
        return "<h1>в вашем имени есть недопустимые символы</h1>"
    
    if (len(username) < 4 or len(username) > 18):
        return "<h1>в ваше имя не должно содержать менее 4 и более 18 символов</h1>"
    
    if (username in content.keys()):
        return "<h1>имя аккаунта уже занято</h1>"

    password = request.form["password"]

    with open("database/accounts.json", "r") as file:
        accounts = json.load(file)

        if (username in accounts.keys()):
            return "user is registered"
            
        else:
            User("database/accounts.json").set_user(
                username=username, 
                password=password,
            )
            return render_template("index.html")
        
@app.route("/create", methods=["GET", "POST"])
def create_post():
    if (request.method == "POST"):
        title = request.form["title"]
        content = request.form["content"]
        post = {'title': title, 'content': content, "username": session.get("username"), 'comments': []}
        posts.append(post)

        with open("database/posts.json", "r") as file:
            posts1 = json.load(file)

            posts1["posts"].append(post)

        with open("database/posts.json", "w") as file:
            json.dump(posts1, file)

    try:
        return render_template("create.html", username=session["username"], moderators=moderators)
    except KeyError:
        return "<h1>вы не вошли в аккаунт</h1>"

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def view_post(post_id):
    post = posts[post_id]
    if (request.method == "POST"):
        comment = request.form["comment"]
        post["comments"].append({"username": session.get("username"), "comment": comment})
    return render_template("view.html", post=post, post_id=post_id, username=session["username"], moderators=moderators)

@app.route("/chat")
def chat1():
    return render_template("main.html", messages=messages, posts=len(posts))

@app.route("/send", methods=["POST"])
def send():
    message = request.form["message"]
    messages.append({"username": session.get("username"), "message": message})
    return render_template("main.html", messages=messages, username=session.get("username"),  moderators=moderators)

@app.route("/login", methods=["GET", "POST"])
def login():
    if (request.method == "POST"):
        session["username"] = request.form["username"]
        password = request.form["password"]

        with open("database/accounts.json", "r") as file:
            accounts = json.load(file)

            for user in accounts:
                if (session["username"] in accounts.keys()):
                    if (password == accounts[user]["password"]):
                        print(session["username"] + " loggined")
                        return redirect("/index") #, messages=messages, username=session.get("username"),  moderators=moderators

                else:
                    return "такого аккаунта не существует!"
                
    return render_template("login.html")

@app.route("/profile/<username>")
def profile(username):

    global userdata

    with open("database/accounts.json", "r") as file:
        users = json.load(file)

        global userdata

        if (username not in users.keys()):
            return "errors/profile_error.html"
        else:
            userdata = {
                "author_username": session.get("username"),
                "username": username,
                "followers": len(users[username]["followers"]),
                "description": users[username]["description"]
            }
            return render_template("profile.html", userdata=userdata, moderators=moderators)
        
@app.route("/profile/<username>/follow", methods=["POST"])
def follow(username):

    with open("database/accounts.json", "r") as file:
        users = json.load(file)

        if (username not in users.keys()):
            return "errors/profile_error.html"
        else:
            if (session.get("username") in users[username]["followers"]):
                return "<h1>вы уже подписаны!</h1>"
            if (username == session.get("username")):
                return "<h1>вы не можете подписаться на себя!</h1>"
            
            file.close()

        with open("database/accounts.json", "w") as file:

            users[username]["followers"].append(session.get("username"))
            json.dump(users, file)

        return render_template("profile.html",  follower=session.get("username"), moderators=moderators, userdata=userdata)

@app.route("/myprofile")
def myprofile():

    with open("database/accounts.json", "r") as file:
        users = json.load(file)

    return render_template("profile_settings.html", followers=len(users[session.get("username")]["followers"]), description=users[session.get("username")]["description"], user=session.get("username"), moderators=moderators)

@app.route("/myprofile_", methods=["POST"])
def myprofile_():
    username = request.args.get("username")
    description = request.form["description"]

    with open("database/accounts.json", "r") as file:
        users = json.load(file)        

    users[session.get("username")]["description"] = description

    with open("database/accounts.json", "w") as file:
        json.dump(users, file)
    
    return render_template("profile_settings.html", followers=len(users[session.get("username")]["followers"]), description=users[session.get("username")]["description"], user=session.get("username"), moderators=moderators)

@app.route("/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):

    if (session["username"] in moderators):
        del posts[post_id]
        return redirect("/index")
    else:
        return "<h1>ошибка</h1>"
    
if (__name__ == "__main__"):
    app.run(host=config["host"], port=config["port"], debug=False)
    