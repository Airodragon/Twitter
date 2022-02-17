# from __init__ import db,login_manager
from email.policy import default
from modules import db,login_manager
from sqlalchemy.orm import backref #It create a pseudo coulmn in child table
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id): #by using userid it will return all the info about the user
    return User.query.get(user_id) #select * from user where id=user_id 

class User(UserMixin,db.Model): # creating a User table in the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    profile_image = db.Column(db.String(100), nullable=False, default='default.jpg')
    background_image = db.Column(db.String(100), nullable=False, default='default_bg.jpg')  
    bio = db.Column(db.String(280), nullable=False, default='New to twitter')
    date = db.Column(db.String(20))
    bday = db.Column(db.String(20))

    posts = db.relationship('Post', backref='author', lazy=True) #lazy=True means it will not load the data until it is needed
    retweeted = db.relationship('Retweet', backref='retweeter', lazy=True)
    bookmark = db.relationship('Bookmark', backref='saved_by', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tweet = db.Column(db.String(500), nullable=False)
    stamp = db.Column(db.String(20), nullable=False)
    post_img = db.Column(db.String(20))
    post_vid = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.Column(db.Integer, nullable=False, default=0)

    commentors = db.relationship('Comments', backref='comment_by', lazy=True)
    likers = db.relationship('Likes', backref='liked_by', lazy=True)
    retweet = db.relationship('Retweet', backref='ori_post', lazy=True)
    timeline = db.relationship('Timeline', backref='from_post', lazy=True)
    bookmark = db.relationship('Bookmark', backref='saved_post', lazy=True)


class Retweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    retweet_stamp = db.Column(db.String(20), nullable=False)
    retweet_text = db.Column(db.String(500), nullable=False)

    likes = db.Column(db.Integer, nullable=False, default=0)
    likers = db.relationship('Likes',backref = 'rt_liked_by',lazy=True)
    commentors = db.relationship('Comments', backref='rt_comment_by', lazy=True)
    timeline = db.relationship('Timeline', backref='from_retweet', lazy=True)

class Timeline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'),default = None)
    retweet_id = db.Column(db.Integer, db.ForeignKey('retweet.id'),default = None)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'),default = None)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),default = None)

class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'),default = None)
    retweet_id = db.Column(db.Integer, db.ForeignKey('retweet.id'),default = None)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),default = None)
    liker  = db.Column(db.String(20), default=None)

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'),default = None)
    retweet_id = db.Column(db.Integer, db.ForeignKey('retweet.id'),default = None)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),default = None)
    comment = db.Column(db.String(240))
    commenter = db.Column(db.String(20),default = None)
    comment_stamp = db.Column(db.String(20), nullable=False)

db.create_all()