from flask import Flask, render_template, request, redirect, url_for, flash, session
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


# ------------------ Landing ------------------
@app.route("/")
def landing():
    return render_template("landing.html")


# ------------------ Signup ------------------
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
        session["active_profile_id"] = profile.id
        return redirect(url_for("profiles"))

    return render_template("signup.html")


# ------------------ Login ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # Auto-select first profile if available
            first_profile = Profile.query.filter_by(user_id=user.id).first()
            if first_profile:
                session["active_profile_id"] = first_profile.id
            return redirect(url_for("profiles"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")


# ------------------ Logout ------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("active_profile_id", None)
    return redirect(url_for("landing"))


# ------------------ Profile Selection ------------------
@app.route("/profiles")
@login_required
def profiles():
    profiles = Profile.query.filter_by(user_id=current_user.id).all()
    return render_template("profiles.html", profiles=profiles, extra_css="style_profiles.css")


# ------------------ Add Profile ------------------
@app.route("/profile/add", methods=["GET", "POST"])
@login_required
def add_profile():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form.get("age") or None
        gender = request.form.get("gender") or None
        conditions = request.form.get("conditions") or ""

        new_profile = Profile(
            user_id=current_user.id,
            name=name,
            age=age,
            gender=gender,
            conditions=conditions,
        )
        db.session.add(new_profile)
        db.session.commit()

        session["active_profile_id"] = new_profile.id
        flash("Profile created successfully!", "success")
        return redirect(url_for("profiles"))

    return render_template("profile_manage.html", profile=None, extra_css="style_profiles.css")


# ------------------ Manage Profile ------------------
@app.route("/profile/<int:profile_id>", methods=["GET", "POST"])
@login_required
def profile_manage(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if profile.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("profiles"))

    if request.method == "POST":
        profile.name = request.form["name"]
        profile.age = request.form.get("age") or None
        profile.gender = request.form.get("gender") or None
        profile.conditions = request.form.get("conditions") or ""
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profiles"))

    return render_template("profile_manage.html", profile=profile, extra_css="style_profiles.css")


# ------------------ Delete Profile ------------------
@app.route("/profile/delete/<int:profile_id>", methods=["POST"])
@login_required
def delete_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if profile.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("profiles"))

    db.session.delete(profile)
    db.session.commit()
    flash("Profile deleted successfully!", "info")

    # reset active profile if it was deleted
    if session.get("active_profile_id") == profile_id:
        first_profile = Profile.query.filter_by(user_id=current_user.id).first()
        session["active_profile_id"] = first_profile.id if first_profile else None

    return redirect(url_for("profiles"))


# ------------------ Set Active Profile ------------------
@app.route("/set_active_profile/<int:profile_id>")
@login_required
def set_active_profile(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if profile.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("profiles"))

    session["active_profile_id"] = profile.id
    return redirect(url_for("chat", profile_id=profile.id))


# ------------------ Chat ------------------
@app.route("/chat/<int:profile_id>", methods=["GET", "POST"])
@login_required
def chat(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if profile.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for("profiles"))

    session["active_profile_id"] = profile.id
    chatbot = HealthChatbot()

    if request.method == "POST":
        user_message = request.form["message"]
        response = chatbot.get_response(user_message)

        chat_entry = Chat(profile_id=profile.id, message=user_message, response=response)
        db.session.add(chat_entry)
        db.session.commit()

    chats = Chat.query.filter_by(profile_id=profile.id).all()
    return render_template("chat.html", profile=profile, chats=chats, extra_css="style_chat.css")


# ------------------ Run ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
