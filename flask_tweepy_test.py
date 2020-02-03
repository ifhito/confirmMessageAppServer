# -*- coding: utf-8 -*-
#
#   flask-tweepy.py
#
#                   Dec/03/2018
#
# ------------------------------------------------------------------
"""
Flask+TweepyによるTwitter連携アプリのサンプル．
連携アプリ認証を行いタイムラインを表示する．
"""
import os
import json
import sys
import tweepy
from flask import Flask, session, redirect, render_template, request, jsonify, abort, make_response
from flask_cors import CORS, cross_origin
from os.path import join, dirname
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import *
from sqlalchemy import exc
import os
import datetime
import time
from datetime import datetime
engine = sqlalchemy.create_engine('sqlite:///dbfile/flaskTweet.sqlite3', echo=False)
app = Flask(__name__)
Base = declarative_base()
class Entry(Base):
    __tablename__ = "confirm"
    userID = Column("userID", String, nullable=False)
    ID = Column('id', String, primary_key = True)
    access_token = Column("access_token", String, nullable=False)
    access_token_secret = Column("access_token_secret", String, nullable=False)
    confirmType = Column("confirmType", String, nullable=False)
    name = Column("name", String, nullable=False)
    message = Column("message",String, nullable=False)
    confirmNum = Column("confirmNum", Integer, nullable=False)
    verificationNum = Column("verificationNum", Integer, nullable=False)
Base.metadata.create_all(bind=engine)
DBSession = sessionmaker(
    autocommit = False,
    autoflush = True,
    bind = engine)
dbSession = DBSession()
app = Flask(__name__)
CORS(app)
app.secret_key = "HvonjvTDDllnFkcnKJbvT6i,lnJYFY"
# --------------------------------------------------------------------------

CONSUMER_KEY = "zCyKug9CJw1BpJH5B8T6Nj2Jh"
CONSUMER_SECRET = "4wayvGG4eCUv3PVRyT73O8uWtTUGkrl7HhxbgdFJlWathFZV6j"

# --------------------------------------------------------------------------
# @app.route('/')
# def index():
#     sys.stderr.write("*** root *** start ***\n")
#     """ root ページの表示 """
#     # 連携アプリ認証済みなら user の timeline を取得
#     timeline = user_timeline()

#     # templates/index.html を使ってレンダリング．
#     sys.stderr.write("*** root *** end ***\n")
#     return render_template('index.html', timeline=timeline)

@app.route("/oath", methods=["GET"])
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
    #websocketでurlを送り返す
    #return無いとエラーが出るため
    return redirect_url

def getUserId(auth):
    api = tweepy.API(auth)
    me = api.me()
    return me.id

@app.route("/twitter", methods=['GET'])
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
        return redirect("http://localhost:3000/TwitterForm" + "?Id={}".format(str(unix)))
    except exc.IntegrityError as e:
        print(e)
    #認証情報をCookieに保存
    # response = make_response(redirect('http://localhost:3000/TwitterForm'))
    # max_age = 60 * 60 * 24 * 120 # 120 days
    # expires = int(datetime.now().timestamp()) + max_age
    # print(auth.access_token, auth.access_token_secret, userId)
    # response.set_cookie('oauth_token', value = str(auth.access_token),max_age=max_age, expires=expires,httponly=False, domain='127.0.0.1')
    # response.set_cookie('oauth_token_secret', value=str(auth.access_token_secret),max_age=max_age, expires=expires, httponly=False, domain='127.0.0.1')
    # response.set_cookie('name', value=str(userId), max_age=max_age, expires=expires, httponly=False, domain='127.0.0.1')

@app.route("/get_name", methods=["GET"])
def get_name():
    res = request.args
    Id = res.get("id")
    print(Id)
    answer = dbSession.query(Entry).filter(Entry.ID == str(Id)+ Entry.userID).one()
    name = answer.name
    return jsonify({'name': name})
@app.route("/push_data", methods=["GET"])
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
        return "http://localhost:3000/verificated" + "?Id={}".format(str(Id))
    except Exception as e:
        print(e)
        return "error"

    return 
    # addDataToDatabase(unix, userId, request.form["message"], request.form["count"], request.form["type"], access_token, access_token_secret)

    # # tweepy で Twitter API にアクセス
    # userId= getUserId(auth)
    # now = datetime.datetime.now()
    # unix = int(time.mktime(now.timetuple()))
    # addDataToDatabase(unix, userId, messages["message"], messages["count"], messages["type"], auth.access_token, auth.access_token_secret, ws)

# @app.route('/pipe')
# def pipe():
#    if request.environ.get('wsgi.websocket'):
#        ws = request.environ['wsgi.websocket']
#        while True:
#             message = ws.receive()
#             messages = json.loads(message)
#             # print(message)
#             #ボタンを押すとTwitterがwebsocketで送られるので送られたら発火
#             if "oauthType" in messages and messages["oauthType"] == "Twitter":
#                 auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
#                 try:
#                     # 連携アプリ認証用の URL を取得
#                     redirect_url = auth.get_authorization_url()
#                     session['request_token'] = auth.request_token
#                 except Exception as ee:
#                     # except tweepy.TweepError:
#                     sys.stderr.write("*** error *** twitter_auth ***\n")
#                     sys.stderr.write(str(ee) + "\n")
#                 #websocketでurlを送り返す
#                 ws.send(redirect_url)
#                 #return無いとエラーが出るため
#                 return redirect_url
#             elif "type" in messages and messages["type"] == "Twitter":
#                 # tweepy でアプリのOAuth認証を行う
#                 # Access token, Access token secret を取得
#                 auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
#                 auth.request_token['oauth_token'] = str(messages["oauth_token"])
#                 auth.request_token['oauth_token_secret'] = str(messages["oauth_verifier"])
#                 try:
#                     auth.get_access_token(str(messages["oauth_verifier"]))
#                 except Exception as ee:
#                     print("error", ee)
#                 # tweepy で Twitter API にアクセス
#                 userId= getUserId(auth)
#                 now = datetime.datetime.now()
#                 unix = int(time.mktime(now.timetuple()))
#                 addDataToDatabase(unix, userId, messages["message"], messages["count"], messages["type"], auth.access_token, auth.access_token_secret, ws)
#                 # user_timeline(messages, ws)
#             else:
#                 return ""

@app.route('/sub', methods=['GET'])
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
            dbSession.delete(data)
            dbSession.commit()
        print("ok")
        return "OK"
    except Exception as ee:
        print("error", ee)
    

# def getUserId(auth):
#     api = tweepy.API(auth)
#     me = api.me()
#     return me.id
# # def user_timeline(auths, ws):
# #     # print("session: ", session)
# #     accessKey = selectDataToDatabase(1)
# #     auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
# #     if accessKey == None:
# #         # tweepy でアプリのOAuth認証を行う
# #         verifier = str(auths["oauth_verifier"])
# #         # Access token, Access token secret を取得．
# #         auth.request_token['oauth_token'] = str(auths["oauth_token"])
# #         auth.request_token['oauth_token_secret'] = verifier
# #         try:
# #             auth.get_access_token(verifier)
# #             addDataToDatabase([auth.access_token, auth.access_token_secret])
# #             # session['access_token'] = auth.access_token
# #             # session["access_token_secret"] = auth.access_token_secret
# #             # print("settions: ", session["access_token"], session["access_token_secret"])
# #         except Exception as ee:
# #             print("error", ee)
# #     print("accessKey: ", accessKey.access_token)
# #     auth.set_access_token(accessKey.access_token, accessKey.access_token_secret)
# #     # tweepy で Twitter API にアクセス
# #     api = tweepy.API(auth)

# #     # user の timeline 内のツイートのリストを1件取得して返す
# #     for status in api.user_timeline(count=1):
# #         text = status.text
# #     # user の timeline 内のツイートのリストを1件取得して返す
# #     ws.send(text)

# def addDataToDatabase(unix, name, message, count, type, access_token, access_token_secret):
#     # print("data: ",data)
#     entry = Entry(ID = str(unix), name=str(name), message=str(message), confirmNum=str(count), confirmType=str(type), access_token=str(access_token), access_token_secret=str(access_token_secret))
#     dbSession.add(entry)
#     try:
#         dbSession.commit()
#         return "http://localhost:3000/verification"
#     except exc.IntegrityError as e:
#         print(e)

@app.route("/getData", methods=['GET'])
def selectDataToDatabase():
    res = request.args
    Id = res.get("Id")
    answer = dbSession.query(Entry).filter(Entry.ID == str(Id)+ Entry.userID).one()
    return jsonify({'name': answer.name, "message": answer.message, "confirmNum": answer.confirmNum, "verificationNum": answer.verificationNum})

@app.teardown_appcontext
def session_clear(exception):
    if exception and Session.is_active:
        session.rollback()
    else:
        #session.commit() 最初こうしてたけど、意図して Rollback した際に不具合おきるからなにもしない
        pass
    dbSession.close()
# --------------------------------------------------------------------------
# @app.route('/twitter_auth', methods=['GET'])
# @cross_origin()
# def twitter_auth():
#     redirect_url = ""
#     """ 連携アプリ認証用URLにリダイレクト """
#     # tweepy でアプリのOAuth認証を行う
#     auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
#     try:
#         # 連携アプリ認証用の URL を取得
#         redirect_url = auth.get_authorization_url()
#         # print(auth.request_token)
#         session['request_token'] = auth.request_token
#     except Exception as ee:
# #   except tweepy.TweepError, e:
#         sys.stderr.write("*** error *** twitter_auth ***\n")
#         sys.stderr.write(str(ee) + "\n")

#     # リダイレクト
#     sys.stderr.write("*** twitter_auth *** end ***\n")
#     result = {"result": auth.request_token}
#     return jsonify({'url': redirect_url})
#
# --------------------------------------------------------------------------

def main():
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    # sys.stderr.write('*** app start! ***\n')
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host='0.0.0.0', port=port)
# --------------------------------------------------------------------------