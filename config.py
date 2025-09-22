import os
class Config:
    SECRET_KEY = "super-secret-key"
    SQLALCHEMY_DATABASE_URI = os.getenv( "DATABASE_URL", "sqlite:///healthchatbot.db" )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
