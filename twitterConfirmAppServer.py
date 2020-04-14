# -*- coding: utf-8 -*-
import os
import json
import sys
import tweepy
import hashlib
from flask import Flask, session, redirect, render_template, request, jsonify, abort, make_response
from flask_cors import CORS, cross_origin
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import *
from sqlalchemy import exc
from datetime import datetime
import time
engine = sqlalchemy.create_engine(os.environ['DATABASE_URL'])
app = Flask(__name__)
CORS(app)
Base = declarative_base()
class Entry(Base):
    __tablename__ = "confirm"
    userID = Column("userid", String, nullable=False)
    ID = Column('id', String, primary_key = True)
    access_token = Column("access_token", String, nullable=False)
    access_token_secret = Column("access_token_secret", String, nullable=False)
    confirmType = Column("confirmtype", String, nullable=False)
    name = Column("name", String, nullable=False)
    message = Column("message",String, nullable=False)
    confirmNum = Column("confirmnum", Integer, nullable=False)
    verificationNum = Column("verificationnum", Integer, nullable=False)
Base.metadata.create_all(bind=engine)
DBSession = sessionmaker(
    autocommit = False,
    autoflush = True,
    bind = engine)
dbSession = DBSession()

app.secret_key = ""
# --------------------------------------------------------------------------

CONSUMER_KEY = ""
CONSUMER_SECRET = ""

# --------------------------------------------------------------------------

@app.route("/oath", methods=["GET"])
@cross_origin()
def oath():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    try:
        # 連携アプリ認証用の URL を取得
        redirect_url = auth.get_authorization_url()
        session['request_token'] = auth.request_token
    except Exception as ee:
        # except tweepy.TweepError:
        sys.stderr.write("*** error *** twitter_auth ***\n")
        sys.stderr.write(str(ee) + "\n")
    return redirect_url

def getUserId(auth):
    api = tweepy.API(auth)
    me = api.me()
    return me.id

@app.route("/twitter", methods=['GET'])
@cross_origin()
def twitter():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    verifier = request.args.get('oauth_verifier')
    request_token = request.args.get("oauth_token")
    auth.request_token['oauth_token'] = str(request_token)
    auth.request_token['oauth_token_secret'] = str(verifier)
    try:
        auth.get_access_token(str(verifier))
    except Exception as ee:
        print("error", ee)
    now = datetime.now()
    unix = int(time.mktime(now.timetuple()))
    userId= getUserId(auth)
    api = tweepy.API(auth)
    userName = api.get_user(userId)
    entry = Entry(ID = str(unix) + str(userId), userID = str(userId), name=str(userName.name), access_token=str(auth.access_token), access_token_secret=str(auth.access_token_secret))
    dbSession.add(entry)
    try:
        dbSession.commit()
        return redirect("https://adoring-dubinsky-d79ae4.netlify.com/TwitterForm" + "?Id={}".format(str(unix)))
    except exc.IntegrityError as e:
        print(e)

@app.route("/get_name", methods=["GET"])
@cross_origin()
def get_name():
    res = request.args
    Id = res.get("id")
    print(Id)
    answer = dbSession.query(Entry).filter(Entry.ID == str(Id)+ Entry.userID).one()
    name = answer.name
    return jsonify({'name': name})

@app.route("/push_data", methods=["GET"])
@cross_origin()
def push_data():
    res = request.args
    Id = res.get('id')
    print(Id)
    message = res.get("message")
    count = res.get("count")
    Type = res.get("type")
    try:
        answer = dbSession.query(Entry).filter(Entry.ID == str(Id)+ Entry.userID).one()
        answer.message = message
        answer.confirmNum = count
        answer.verificationNum = 0
        answer.confirmType = Type
        dbSession.commit()
        return "https://adoring-dubinsky-d79ae4.netlify.com/verificated" + "?Id={}".format(str(Id))
    except Exception as e:
        print(e)
        return "error"

    return 

@app.route('/sub', methods=['GET'])
@cross_origin()
def sub():
    try:
        res = request.args
        print(res)
        Id = res.get("Id")
        data = dbSession.query(Entry).filter(Entry.ID == str(Id)+ Entry.userID).one()
        data.verificationNum = data.verificationNum + 1
        dbSession.add(data)
        dbSession.commit()
        print(data.verificationNum)
        if data.confirmNum <= data.verificationNum:
            auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
            auth.set_access_token(data.access_token, data.access_token_secret)
            api = tweepy.API(auth)
            api.update_status(data.message)
            dbSession.commit()
        print("ok")
        return "OK"
    except Exception as ee:
        print("error", ee)
    

@app.route("/getData", methods=['GET'])
@cross_origin()
def selectDataToDatabase():
    res = request.args
    Id = res.get("Id")
    answer = dbSession.query(Entry).filter(Entry.ID == str(Id)+ Entry.userID).one()
    return jsonify({'name': answer.name, "message": answer.message, "confirmNum": answer.confirmNum, "verificationNum": answer.verificationNum})

# @app.teardown_appcontext
# def session_clear(exception):
#     if exception and Session.is_active:
#         session.rollback()
#     else:
#         pass
#     dbSession.close()

def main():
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# --------------------------------------------------------------------------