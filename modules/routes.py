from logging import log
from operator import irshift
from re import U
import re
from types import MethodDescriptorType
from flask import Flask, render_template, redirect, request, url_for, flash, abort
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.sqltypes import Time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import desc
from modules.forms import createTweet
from modules import db, app
from modules.models import User, Post, Timeline, Retweet, Bookmark, Likes, Comments
from modules.forms import Signup, Login, UpdateProfile, createComment, searchNews
from modules.functions import save_tweet_picture, save_bg_picture, save_profile_picture, delete_old_images

######### AUTHENTICATION #########
import datetime
from datetime import date
from newsapi import NewsApiClient


def age(birthdate):
    today = date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age


@app.route('/')
@app.route('/home/', methods = ['GET', 'POST'])
def home():
    form_sign = Signup()
    form_login = Login()
    if form_sign.signup.data and form_sign.validate_on_submit():
        hashed_password = generate_password_hash(form_sign.password.data, method='sha256')
        valid_flag = True
        x = datetime.datetime.now()
        user_birthyear = form_sign.bday.data.year
        user_birthmonth = form_sign.bday.data.month
        user_birthdate = form_sign.bday.data.day
        user_age = age(date(user_birthyear, user_birthmonth, user_birthdate))

        if user_age < 18:
            valid_flag = False
            print("Below age limit")

        users = User.query.all()
        for i in users:
            if form_sign.username.data == i.username:
                valid_flag = False
                print("Username Taken")
            if form_sign.email.data == i.email:
                valid_flag = False
                print("Email already registered")
        
        if not valid_flag:
            return render_template("start.html", form1 = form_sign, form2 = form_login)
        else:    
            creation = str(x.strftime("%B")) + " " + str(x.strftime("%Y"))
            new_user = User(username = form_sign.username.data, email = form_sign.email.data,
                password = hashed_password, bday = form_sign.bday.data, date = creation)
            db.session.add(new_user)
            db.session.commit()
        return render_template("sign.html")

    if form_login.login.data and form_login.validate_on_submit():
        user_info = User.query.filter_by(username = form_login.username.data).first()
        if user_info:
            login_user(user_info, form_login.remember.data)
            if check_password_hash(user_info.password, form_login.password.data):
                return redirect(url_for('dashboard'))
            else:
                return render_template("errorP.html")
        else:
            return render_template("errorU.html")

    return render_template("start.html", form1 = form_sign, form2 = form_login)

@app.route("/logout/")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard/', methods = ['GET','POST'])
def dashboard():
    user_tweet = createTweet()
    if user_tweet.validate_on_submit():

        x = datetime.datetime.now()
        currentTime = str(x.strftime("%d")) + " " + str(x.strftime("%b")) + " " + str(x.strftime("%y")) + " " + str(x.strftime("%I")) + ":" + str(x.strftime("%M")) + " " + str(x.strftime("%p"))

        if user_tweet.tweet_img.data:
            tweet_img = save_tweet_picture(user_tweet.tweet_img.data)
            post = Post(tweet = user_tweet.tweet.data, stamp = currentTime, author = current_user, post_img = tweet_img)
        else:
            post = Post(tweet = user_tweet.tweet.data, stamp = currentTime, author = current_user)
        db.session.add(post)
        db.session.commit()

        to_timeline = Timeline(post_id = post.id)
        db.session.add(to_timeline)
        db.session.commit()

        flash("Tweet added to timeline")
        return redirect(url_for('dashboard'))

    page = request.args.get('page', 1, type = int)
    timeline = Timeline.query.order_by(desc(Timeline.id)).paginate(page = page, per_page = 5)
    return render_template("dashboard.html", name = current_user.username, tweet = user_tweet, timeline = timeline)

@app.route('/view_profile/<int:account_id>', methods = ['GET','POST'])
@login_required
def viewProfile(account_id):
    if account_id == current_user.id:
        return redirect(url_for('account'))
    get_user = User.query.filter_by(id = account_id).first()
    profile_pic = url_for('static', filename = 'Images/Users/profile_pics/' + get_user.profile_image)
    bg_pic = url_for('static', filename = 'Images/Users/bg_pics/' + get_user.background_image)

    page = request.args.get('page', 1, type = int)
    all_posts = Post.query.filter_by(user_id = get_user.id).order_by(desc(Post.id)).paginate(page = page, per_page = 5)
    retweets = Retweet.query.filter_by(user_id = get_user.id).order_by(desc(Retweet.id))


    return render_template('view_profile.html', profile = profile_pic, background = bg_pic, timeline = all_posts, user = get_user, retweets = retweets)
    
@app.route('/bookmark/<int:post_id>', methods = ['GET', 'POST'])
def save_post(post_id):
    saved_post = Bookmark(post_id = post_id, user_id = current_user.id)
    db.session.add(saved_post)
    db.session.commit()
    flash("Post saved to Bookmarks", 'success')

    return redirect(url_for('dashboard'))

@app.route('/unsave_post/<int:postId>', methods = ['GET', 'POST'])
def unsave_post(postId):
    allPosts = Bookmark.query.all()
    for post in allPosts:
        if post.post_id == postId:
            db.session.delete(post)
            db.session.commit()
    flash("Post removed from Bookmarks", 'success')
    return redirect(url_for('dashboard'))

@app.route('/saved_posts/')
def bookmarks():
    posts = Bookmark.query.filter_by(user_id = current_user.id).order_by(desc(Bookmark.id))
    empty = False
    if not posts.first():
        empty = True

    return render_template("bookmarks.html", posts = posts, empty = empty)

@app.route('/account/', methods = ['GET', 'POST'])
@login_required
def account():
    profile_pic = url_for('static', filename = 'Images/Users/profile_pics/' + current_user.profile_image)
    bg_pic = url_for('static', filename = 'Images/Users/bg_pics/' + current_user.background_image)

    page = request.args.get('page', 1, type = int)
    all_posts = Post.query.filter_by(user_id = current_user.id).order_by(desc(Post.id)).paginate(page = page, per_page = 5)
    retweets = Retweet.query.filter_by(user_id = current_user.id).order_by(desc(Retweet.id))

    return render_template('account.html', profile = profile_pic, background = bg_pic, timeline = all_posts, retweets = retweets)

@app.route('/UpdateInfo', methods = ['GET', 'POST'])
@login_required
def updateInfo():
    update = UpdateProfile()
    if update.validate_on_submit():
        old_img = ''
        old_bg_img = ''
        if update.profile.data:
            profile_img = save_profile_picture(update.profile.data)
            old_img = current_user.profile_image
            current_user.profile_image = profile_img
        if update.profile_bg.data:
            bg_img = save_bg_picture(update.profile_bg.data)
            old_bg_img = current_user.background_image
            current_user.background_image = bg_img
        current_user.username = update.username.data
        current_user.email = update.email.data
        current_user.bio = update.bio.data
        db.session.commit()

        delete_old_images(old_img, old_bg_img)
        flash('Your account has been successfully updated')
        return redirect(url_for('account'))

    elif request.method == 'GET':
        update.username.data = current_user.username
        update.email.data = current_user.email
        update.bio.data = current_user.bio   
    return render_template('updateProfile.html', change_form = update)

@app.route('/deactivate_confirmation/')
@login_required
def deactivate_confirm():
    return render_template('deact_conf.html')

@app.route('/account_deleted/<int:account_id>', methods = ['POST'])
@login_required
def delete_account(account_id):
    if current_user.id != account_id:
        abort(403)

    all_retweets = Retweet.query.filter_by(user_id = account_id)
    for i in all_retweets:
        db.session.delete(i)
    all_posts = Post.query.filter_by(user_id = account_id)
    for i in all_posts:
        db.session.delete(i)
    del_acc = User.query.filter_by(id = account_id).first()
    db.session.delete(del_acc)
    db.session.commit()

    timeline_delete = Timeline.query.filter_by(post_id = None, retweet_id = None)
    for i in timeline_delete:
        db.session.delete(i)
    db.session.commit()
    

    return redirect(url_for('home'))

@app.route('/retweet/<int:post_id>', methods = ['GET', 'POST'])
@login_required
def retweet(post_id):
    post = Post.query.get_or_404(post_id)
    new_tweet = createTweet()

    if new_tweet.validate_on_submit():
        x = datetime.datetime.now()
        currentTime = str(x.strftime("%d")) + " " + str(x.strftime("%b")) + " " + str(x.strftime("%y")) + " " + str(x.strftime("%I")) + ":" + str(x.strftime("%M")) + " " + str(x.strftime("%p"))

        retweet = Retweet(tweet_id = post.id, user_id = current_user.id, retweet_stamp = currentTime, retweet_text = new_tweet.tweet.data)
        db.session.add(retweet)
        db.session.commit()

        to_timeline = Timeline(retweet_id = retweet.id)
        db.session.add(to_timeline)
        db.session.commit()

        msg = "Added retweet to @" + post.author.username +" 's tweet."
        flash("msg")
        return redirect(url_for('dashboard'))

    return render_template("retweet.html", post = post, tweet = new_tweet)

@app.route('/delete/<int:post_id>')
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author.id != current_user.id:
        abort(403)

    return render_template('delete_post.html', post = post)

@app.route('/delete_retweet/<int:post_id>')
@login_required
def delete_retweet(post_id):
    retweet = Retweet.query.get_or_404(post_id)
    if retweet.retweeter.id != current_user.id:
        abort(403)

    return render_template('delete_post.html', retweet = retweet)

@app.route('/delete_post/<int:post_id>', methods = ['POST'])
@login_required
def delete_tweet(post_id):
    post_bk = Bookmark.query.filter_by(post_id = post_id)
    if post_bk:
        for i in post_bk:
            db.session.delete(i)
            db.session.commit()

    remove_from_timeline = Timeline.query.filter_by(post_id = post_id).first()
    db.session.delete(remove_from_timeline)
    db.session.commit()

    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash("Your tweet is deleted successfully")

    return redirect(url_for('dashboard'))

@app.route('/delete_retweeted_post/<int:post_id>', methods = ['POST'])
@login_required
def delete_retweeted_tweet(post_id):
    remove_from_timeline = Timeline.query.filter_by(retweet_id = post_id).first()
    if remove_from_timeline.from_retweet.retweeter != current_user:
        abort(403)
    db.session.delete(remove_from_timeline)
    db.session.commit()
    
    post = Retweet.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash("Your retweet is deleted successfully")

    return redirect(url_for('dashboard'))



@app.route('/like_post/<int:post_id>', methods = ['GET','POST'])
@login_required
def like_post(post_id):
    post = Post.query.filter_by(id = post_id).first()
    liked = False
    likeID = -1
    for i in post.likers:
        if i.liker == current_user.username:
            liked = True
            likeID = i.id
    if liked:
        likeToBeRemoved = Likes.query.filter_by(id = likeID).first()
        db.session.delete(likeToBeRemoved)
        post.likes -= 1
        flash("Unliked tweet", 'success')
    else:
        liked_post = Likes(post_id = post_id, user_id = current_user.id, liker = current_user.username)
        db.session.add(liked_post)
        post.likes += 1
        flash("liked tweet", 'success')
    db.session.commit()

    return  redirect(url_for('dashboard'))



@app.route('/like_retweet/<int:post_id>', methods = ['GET','POST'])
@login_required
def like_retweet(post_id):
    retweet = Retweet.query.filter_by(id = post_id).first()
    liked = False
    likeID = -1
    for i in retweet.likers:
        if i.liker == current_user.username:
            liked = True
            likeID = i.id
    
    if liked:
        likeToBeRemoved = Likes.query.filter_by(id = likeID).first()
        db.session.delete(likeToBeRemoved)
        retweet.likes -= 1
        flash("Unliked retweet", 'success')
    else:
        liked_post = Likes(retweet_id = post_id, user_id = current_user.id, liker = current_user.username)
        db.session.add(liked_post)
        retweet.likes += 1
        flash("liked retweet", 'success')
    db.session.commit()
    return redirect(url_for('dashboard'))



@app.route('/comment_post/<int:post_id>', methods = ['GET','POST'])
def comment_post(post_id):
    user_comment = createComment()
    if user_comment.validate_on_submit():
        x = datetime.datetime.now()
        currentTime = str(x.strftime("%d")) + " " + str(x.strftime("%b")) + " " + str(x.strftime("%y")) + " " + str(x.strftime("%I")) + ":" + str(x.strftime("%M")) + " " + str(x.strftime("%p"))
        comment = Comments(post_id = post_id, user_id = current_user.id, comment = user_comment.comment.data,commenter = current_user.username,comment_stamp = currentTime)
        db.session.add(comment)
        db.session.commit()
        flash("Commented Succesfully",'success')
    comments = Comments.query.filter_by(post_id = post_id).all()
    return render_template("comment.html",curr_comment = user_comment, comments = comments,name = current_user.username,curr_post_id = post_id)



@app.route('/comment_retweet/<int:post_id>', methods = ['GET','POST'])
def comment_retweet(post_id):
    user_comment = createComment()
    if user_comment.validate_on_submit():
        x = datetime.datetime.now()
        currentTime = str(x.strftime("%d")) + " " + str(x.strftime("%b")) + " " + str(x.strftime("%y")) + " " + str(x.strftime("%I")) + ":" + str(x.strftime("%M")) + " " + str(x.strftime("%p"))
        comment = Comments(retweet_id = post_id, user_id = current_user.id, comment = user_comment.comment.data,commenter = current_user.username,comment_stamp = currentTime)
        db.session.add(comment)
        db.session.commit()
        flash("Commented Succesfully",'success')
    comments = Comments.query.filter_by(retweet_id = post_id).all()
    return render_template("comment.html",curr_comment = user_comment, comments = comments,name = current_user.username,curr_post_id = post_id)


@app.route('/delete_post_comment/<int:post_id>/<int:comment_id>')
@login_required
def delete_post_comment(comment_id,post_id):
    comment = Comments.query.get_or_404(comment_id)
    if comment.commenter != current_user.username:
        abort(403)
    
    return render_template('deleteComment.html',post_id = post_id, removed_comment = comment)

@app.route('/deletePostComment/<int:post_id>/<int:comment_id>',methods=['GET','POST'])
def deletePostComment(comment_id,post_id):
    removed_comment = Comments.query.filter_by(id = comment_id).first()
    if removed_comment.commenter != current_user.username:
        abort(403)
    db.session.delete(removed_comment)
    db.session.commit()
    flash("Your comment was deleted successfully",'success')
    return redirect(url_for('comment_post',post_id = post_id,type='post'))


@app.route('/delete_rt_comment/<int:post_id>/<int:comment_id>')
@login_required
def delete_rt_comment(comment_id,post_id):
    comment = Comments.query.get_or_404(comment_id)
    if comment.commenter != current_user.username:
        abort(403)
    
    return render_template('deleteComment.html',post_id = post_id, removed_comment = comment)


@app.route('/deleteRetweetComment/<int:retweet_id>/<int:comment_id>',methods=['GET','POST'])
def deleteRetweetComment(comment_id,retweet_id):
    removed_comment = Comments.query.filter_by(id = comment_id).first()
    if removed_comment.commenter != current_user.username:
        abort(403)
    db.session.delete(removed_comment)
    db.session.commit()
    flash("Your comment was deleted successfully",'success')
    return redirect(url_for('comment_retweet',post_id = retweet_id,type='post'))


@app.route('/news', methods = ['GET','POST'])
def news():
    query = searchNews()
    all_articles=[]
    if query.validate_on_submit():
        newsapi = NewsApiClient(api_key='c2d72a4ef82d4304a5aa8eff2bf67a90')
        all_articles = newsapi.get_everything(q=query.query.data)
    return render_template('news.html',query=query,news=all_articles)