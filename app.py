from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Profile, Chat
from chatbot import HealthChatbot

app = Flask(__name__)
app.config.from_object(Config)

# Init DB
db.init_app(app)

# Login Manager
login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def landing():
    return render_template("landing.html")

# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        phone = request.form["phone"]
        password = generate_password_hash(request.form["password"], method="pbkdf2:sha256")

        user = User(email=email, phone=phone, password_hash=password)
        db.session.add(user)
        db.session.commit()

        # Default profile
        profile = Profile(user_id=user.id, name=name)
        db.session.add(profile)
        db.session.commit()

        login_user(user)
        return redirect(url_for("profiles"))

    return render_template("signup.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("profiles"))
        flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("landing"))

@app.route("/profiles")
@login_required
def profiles():
    profiles = Profile.query.filter_by(user_id=current_user.id).all()
    return render_template("profiles.html", profiles=profiles)

@app.route("/chat/<int:profile_id>", methods=["GET", "POST"])
@login_required
def chat(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    chatbot = HealthChatbot()

    if request.method == "POST":
        user_message = request.form["message"]
        response = chatbot.get_response(user_message)

        chat_entry = Chat(profile_id=profile.id, message=user_message, response=response)
        db.session.add(chat_entry)
        db.session.commit()

    chats = Chat.query.filter_by(profile_id=profile.id).all()
    return render_template("chat.html", profile=profile, chats=chats)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)

