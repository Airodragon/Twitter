from typing import Text
from flask_wtf import FlaskForm
from werkzeug import datastructures
from wtforms import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.fields import DateField
from flask_wtf.file import FileAllowed, FileField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from modules.models import User
from flask_login import current_user

class Signup(FlaskForm):
    username = StringField('Username', validators = [DataRequired(), Length(min = 4)])
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Passowrd', validators = [DataRequired(), Length(min = 6)])
    bday = DateField('Add your birthday')
    signup = SubmitField('Sign up')

    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()
        if user:
            print("Username already taken")
            raise ValidationError("Username is already taken")
    
    def validate_email(self, email):
        user = User.query.filter_by(email = email.data).first()
        if user:
            print("Email already registered")
            raise ValidationError("Email already registered")
        
class Login(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
    remember = BooleanField('Remember me')
    login = SubmitField('Login')

class createTweet(FlaskForm):
    tweet = TextAreaField("What\'s on your mind?", validators = [DataRequired(), Length(max = 280)])
    tweet_img = FileField("Include image", validators = [FileAllowed(['jpg', 'jpeg', 'png','gif'])])
    tweet_vid = FileField("Include video",validators=[FileAllowed(['mp4'])])
    submit = SubmitField("Tweet")

class UpdateProfile(FlaskForm):
    username = StringField('Username', validators = [Length(min = 4)])
    email = StringField('Email', validators = [Email()])
    bio = StringField('Tell us a little about yourself', validators = [Length(max = 100)])
    profile = FileField('Update profile picture', validators = [FileAllowed(['jpg', 'jpeg', 'png'])])
    profile_bg = FileField('Update profile background', validators = [FileAllowed(['jpg', 'jpeg', 'png'])])
    save = SubmitField('Save changes')

    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()
        if user and user.id != current_user.id:
            print("Username already taken")
            raise ValidationError("Username is already taken")
    
    def validate_email(self, email):
        user = User.query.filter_by(email = email.data).first()
        if user and user.email != current_user.email:
            print("Email already registered")
            raise ValidationError("Email already registered")

class createComment(FlaskForm):
    comment = TextAreaField("Tweet your reply",validators=[DataRequired(), Length(max = 280)])
    submit = SubmitField("Comment")

class searchNews(FlaskForm):
    query = TextAreaField('Search here', validators = [DataRequired(),Length(max = 10)])
    submit = SubmitField('Search')