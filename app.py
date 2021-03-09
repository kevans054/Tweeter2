from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import json
import dbcreds
import mariadb
import uuid
import random
import datetime

app = Flask(__name__)
CORS(app)

def connection():
    return mariadb.connect(
        user = dbcreds.user,
        password = dbcreds.password,
        host = dbcreds.host,
        port = dbcreds.port,
        database = dbcreds.database   
    )
def resolve_login_token(loginToken):
    conn = None
    cursor = None
    userId = None
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT userId from user_session WHERE loginToken=?", [loginToken])
    userId = cursor.fetchone()[0]
    print("inside the loginToken function", userId)
    return userId

def resolve_username(userId):
    conn = None
    cursor = None
    username = None
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username from user WHERE userId=?", [userId])
    username = cursor.fetchone()[0]
    print("inside the username function", username)
    return username

@app.route('/api/users', methods=["GET", "POST", "DELETE", "PATCH"])
def users():
#   GET A USER(S)
    if request.method == 'GET':
        conn = None
        cursor = None
        result = None
        userId = request.args.get("userId")
        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user WHERE userId=?", [userId])
            result = cursor.fetchone()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close() 
                return Response(
                    json.dumps(result, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem finding that user.",
                    mimetype="text/html",
                    status=500
                )

#   CREATE A NEW USER
    elif request.method == 'POST':
        conn = None
        cursor = None
        result = None
        userId = None
        parameters = request.get_json()
        email = parameters["email"]
        username = parameters["username"]
        password = parameters["password"]
        bio = parameters["bio"]
        birthdate = parameters["birthdate"]
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user(email, username, password, bio, birthdate) VALUES(?, ?, ?, ?, ?)", [email, username, password, bio, birthdate])
            conn.commit()
            result = cursor.rowcount
            userId = cursor.lastrowid
            if(result == 1):
                loginToken = str(uuid.uuid4())
                try:
                    print(userId, loginToken)
                    cursor.execute("INSERT INTO user_session(userId, loginToken) VALUES(?, ?)", [userId, loginToken])
                    conn.commit()
                except Exception as ex:
                    return Response("The action was unsuccessful.", ex)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(result == 1):
                user = {
                    "userId": userId,
                    "email": email,
                    "username": username,
                    "bio": bio,
                    "birthdate": birthdate,
                    "loginToken": loginToken
                    }
                return Response(
                    json.dumps(user, default=str),
                    mimetype = "application/json",
                    status=200
                ) 
            else: 
                return Response(
                    "There was a problem creating a new user.",
                    mimetype="text/html",
                    status=500
                )

#   UPDATE A USER
    elif request.method == 'PATCH':
        conn = None
        cursor = None
        result = None
        user = None
        parameters = request.get_json()
        bio = parameters["bio"]
        loginToken = parameters["loginToken"]
        print(loginToken)
        userId = resolve_login_token(loginToken)
        print(userId)
        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("UPDATE user SET bio=? WHERE userId=?", [bio, userId])
            result = cursor.rowcount
            print(result)
            conn.commit()
            cursor.execute("SELECT * FROM user WHERE userId=?", [userId])
            user = cursor.fetchone()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    json.dumps(user, default=str),
                    mimetype = "application/json",
                    status=200
                ) 
            else: 
                return Response(
                    "There was a problem editing that user record.",
                    mimetype="text/html",
                    status=500
                )


#   DELETE A USER
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        result = None
        parameters = request.get_json()
        password = parameters["password"]
        loginToken = parameters["loginToken"]
        userId = resolve_login_token(loginToken)
        print(userId)
        print(loginToken)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user WHERE userId=?", [userId])
            result = cursor.rowcount
            conn.commit()
            print(result)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    "Your account has been deleted",
                    mimetype = "html/text",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem deleting that user.",
                    mimetype="text/html",
                    status=500
                )
            

@app.route('/api/login', methods=["POST", "DELETE"])
def login():
#   LOGIN
    if request.method == 'POST':
        conn = None
        cursor = None
        parameters = request.get_json()
        username = parameters["username"]
        password = parameters["password"]
        userdata = None
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE username=? AND password=?", [username, password])
            userdata = cursor.fetchone()
            userId = userdata[0]
            loginToken = str(uuid.uuid4())
            if(userdata != None):
                userdata = {
                    "userId": userId,
                    "email": userdata[2],
                    "username": username,
                    "bio": userdata[3],
                    "birthdate": userdata[4],
                    "loginToken": loginToken
                    }
            try:
                cursor.execute("INSERT INTO user_session(loginToken, userId) VALUES(?, ?)", [loginToken, userId])
                result = cursor.rowcount
                conn.commit()
            except Exception as ex:
                return Response("The action was unsuccessful.", ex)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    json.dumps(userdata, default=str),
                    mimetype="application/json",
                    status=500
                )
            else: 
                return Response(
                    "There was a problem deleting that user.",
                    mimetype="text/html",
                    status=500
                )


#   LOGOUT
    if request.method == 'DELETE':
        conn = None
        cursor = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_session WHERE loginToken=?", [loginToken])
            result = cursor.rowcount
            conn.commit()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                  "You logged out",
                  mimetype = "html/text",
                  status=200
                 )
            else: 
                return Response(
                    "There was a problem logging out.",
                    mimetype="text/html",
                    status=500
                )

@app.route('/api/follows', methods=["GET","POST", "DELETE"])
def follows():
    #GET FOLLOWERS
    if request.method == 'GET':
        conn = None
        cursor = None
        result = None
        userId = request.args.get("userId")
        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM follows WHERE follower=?", [userId])
            result = cursor.fetchall()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close() 
                return Response(
                    json.dumps(result, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
#POST A FOLLOW
    elif request.method == 'POST':
        conn = None
        cursor = None
        result = None
#         userId to be followed
        parameters = request.get_json()
        followId = parameters["followId"]
#         user that wants to follow another
        loginToken =parameters["loginToken"]
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_session WHERE loginToken=?", [loginToken])
            follower = cursor.fetchone()[0]
            try:
                cursor.execute("INSERT INTO follows(followId, follower) VALUES(?, ?)", [followId, follower])
                result = cursor.rowcount
                conn.commit()
            except Exception as ex:
                return Response("The action was unsuccessful.", ex)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                  "You are now following: ",
                  mimetype = "html/text",
                  status=200
                 )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
#DELETE A FOLLOW
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        result = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        follower = resolve_login_token(loginToken)
        followId = parameters["followId"]
        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("DELETE FROM follows WHERE follower=? AND followId=?", [follower, followId])
            result = cursor.rowcount
            conn.commit()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    "You are no longer following: ",
                    mimetype = "html/text",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )

@app.route('/api/followers', methods=["GET","POST", "DELETE"])
def followers():
    if request.method == 'GET':
        conn = None
        cursor = None
        followId = request.args.get("userId")
        print(followId)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("SELECT userId, email, username, bio, birthdate FROM user JOIN follows ON user.userId = follows.follower WHERE followId=?", [followId])
            result = cursor.fetchall()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close() 
                return Response(
                    json.dumps(result, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )

@app.route('/api/tweets', methods=["GET","POST", "DELETE", "PATCH"])
def tweets():
    # GET A TWEET
    if request.method == 'GET':
        conn = None
        cursor = None
        result = None
        tweetId = None
        content = None
        createdAt = None
        userId = request.args.get("userId")
        print(userId)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM user WHERE userId=?", [userId])
            username = cursor.fetchall()[0]
            print(username)
            cursor.execute("SELECT tweetId, content, createdAt FROM tweet WHERE userId=?", [userId])
            result = cursor.fetchall()
            print(result)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                if userId != None:
                    tweets=[]
                    for row in result:
                        tweetdetails = {
                            "tweetId": result[0][0],
                            "userId": userId,
                            "username": username[0],
                            "content": result[0][1],
                            "createdAt": result[0][2]
                        }
                    tweets.append(tweetdetails)
                    print(tweets)
                return Response(
                    json.dumps(tweets, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
    #POST A TWEET
    elif request.method == 'POST':
        conn = None
        cursor = None
        result = None
        userId = None
        tweetId = None
        username = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        content = parameters["content"]
        createdAt = datetime.datetime.now()
        print(createdAt)
        print(loginToken)
        print(content)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user.userId, user.username FROM user JOIN user_session ON user_session.userId=user.userId WHERE loginToken=?", [loginToken])
            user = cursor.fetchall()
            print(user)
            if (len(user) == 1):
                cursor.execute("INSERT INTO tweet (content, userId, createdAt) VALUES(?, ?, ?)", [content, user[0][0], createdAt])
                conn.commit()
                tweetId = cursor.lastrowid

        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                if tweetId != None:
                    tweetdetails = {
                        "tweetId": tweetId,
                        "userId": user[0][0],
                        "username": user[0][1],
                        "content": content,
                        "createdAt": createdAt
                    }
                    return Response(
                        json.dumps(tweetdetails, default=str),
                        mimetype = "application/json",
                        status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
    # DELETE A TWEET
    elif request.method == 'DELETE':
            conn = None
            cursor = None
            result = None
            parameters = request.get_json()
            loginToken = parameters["loginToken"]
            userId = resolve_login_token(loginToken)
            print(userId)
            print(loginToken)
            tweetId = parameters["tweetId"]
            print(tweetId)
            try:
                conn = connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tweet WHERE userId=? AND tweetId=?", [userId, tweetId])
                result = cursor.rowcount
                print(result)
                conn.commit()
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)  
            finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                    return Response(
                        "Your tweet has been deleted. ",
                        mimetype = "html/text",
                        status=200
                    )
                else: 
                    return Response(
                        "There was a problem completing the request.",
                        mimetype="text/html",
                        status=500
                    )
        
#   UPDATE A TWEET
    elif request.method == 'PATCH':
        conn = None
        cursor = None
        result = None
        parameters = request.get_json()
        tweetId = parameters["tweetId"]
        loginToken = parameters["loginToken"]
        content = parameters["content"]
        createdAt = datetime.datetime.now() 
        userId = resolve_login_token(loginToken)
        print(loginToken)
        print(userId)
        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("UPDATE tweet SET content=? WHERE tweetId=?", [content, tweetId])
            rowcount = cursor.rowcount
            print(rowcount)
            conn.commit()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                result = {
                    "tweetId": tweetId,
                    "content": content
                }
                return Response(
                    json.dumps(result, default=str),
                    mimetype = "application/json",
                    status=200
                ) 
            else: 
                return Response(
                    "There was a problem editing that user record.",
                    mimetype="text/html",
                    status=500
                )
# TWEET-LIKES
@app.route('/api/tweet-likes', methods=["GET","POST", "DELETE", "PATCH"])
def tweetlikes():
    # GET A TWEET-LIKE
    if request.method == 'GET':
        conn = None
        cursor = None
        result = None
        userId = None
        username = None
        tweetId = request.args.get("tweetId")
        print(tweetId)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM tweet WHERE tweetId=?", [tweetId])
            userId = cursor.fetchone()[0]
            print(userId)
            username = resolve_username(userId)
            print(username)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                if userId != None:
                    result = {
                        "tweetId": tweetId,
                        "userId": userId,
                        "username": username,
                    }
                    print(result)
                return Response(
                    json.dumps(result, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
    #POST A TWEET-LIKE
    elif request.method == 'POST':
        conn = None
        cursor = None
        result = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        TlikeId = resolve_login_token(loginToken)
        tweetId = parameters["tweetId"]
        print(loginToken)
        print(tweetId)
        print(TlikeId)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tweet_like (tweetId, TlikeId) VALUES(?, ?)", [tweetId, TlikeId])
            result = cursor.rowcount
            print(result)
            conn.commit()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                ("You liked tweet: ", tweetId),
                mimetype = "application/json",
                status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
    # DELETE A TWEET-LIKE
    elif request.method == 'DELETE':
            conn = None
            cursor = None
            result = None
            parameters = request.get_json()
            loginToken = parameters["loginToken"]
            TlikeId = resolve_login_token(loginToken)
            print(TlikeId)
            print(loginToken)
            tweetId = parameters["tweetId"]
            print(tweetId)
            try:
                conn = connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tweet_like WHERE TlikeId=? AND tweetId=?", [TlikeId, tweetId])
                result = cursor.rowcount
                print(result)
                conn.commit()
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)  
            finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                    return Response(
                        "Your tweet-like has been deleted. ",
                        mimetype = "html/text",
                        status=200
                    )
                else: 
                    return Response(
                        "There was a problem completing the request.",
                        mimetype="text/html",
                        status=500
                    )

@app.route('/api/comments', methods=["GET", "POST", "DELETE", "PATCH"])
def comment():
#   GET COMMENT(S)
    if request.method == 'GET':
        conn = None
        cursor = None
        comments = None
        tweetId = request.args.get("tweetId")
        print("tweetId is: ", tweetId)
        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            if (tweetId != None):
                cursor.execute("SELECT comment.*, user.username FROM comment JOIN user ON comment.userId = user.userId WHERE comment.tweetId=?", [tweetId])
                comments = cursor.fetchall()
                print("Result: ", comments)
            elif (tweetId == None):
                cursor.execute("SELECT * FROM comment")
                comments = cursor.fetchall()
                print("Result: ", comments)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    json.dumps(comments, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem finding that comment.",
                    mimetype="text/html",
                    status=500
                )

#   CREATE A NEW COMMENT
    elif request.method == 'POST':
        conn = None
        cursor = None
        commentId = None
        parameters = request.get_json()
        tweetId = parameters["tweetId"]
        loginToken = parameters["loginToken"]
        content = parameters["content"]
        userId = resolve_login_token(loginToken)
        username = resolve_username(userId)
        createdAt = datetime.datetime.now()
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO comment(tweetId, content, createdAt, userId) VALUES(?, ?, ?, ?)", [tweetId, content, createdAt, userId])
            commentId = cursor.lastrowid
            conn.commit()
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(commentId != None):
                comment = {
                    "commentId": commentId,
                    "tweetId" : tweetId,
                    "userId": userId,
                    "username": username,
                    "content": content,
                    "createdAt": createdAt
                    }
                return Response(
                    json.dumps(comment, default=str),
                    mimetype = "application/json",
                    status=200
                ) 
            else: 
                return Response(
                    "There was a problem creating a new comment.",
                    mimetype="text/html",
                    status=500
                )

#   UPDATE A COMMENT
    elif request.method == 'PATCH':
        conn = None
        cursor = None
        result = None
        user = None
        parameters = request.get_json()
        commentId = parameters["commentId"]
        new_content = parameters["content"]
        createdAt = datetime.datetime.now()
        loginToken = parameters["loginToken"]
        print(loginToken)
        userId = resolve_login_token(loginToken)
        print(userId)
        try:
            conn = connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("UPDATE comment SET content=? WHERE userId=?", [new_content, userId])
            rowcount = cursor.rowcount
            conn.commit()
            print(rowcount)
            if (rowcount != None):
                cursor.execute("SELECT comment.*, user.username FROM user JOIN comment ON user.userId = comment.userId WHERE comment.commentId=?", [commentId])
                result = cursor.fetchall()
                print("Result is: ", result)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    json.dumps(result, default=str),
                    mimetype = "application/json",
                    status=200
                ) 
            else: 
                return Response(
                    "There was a problem editing that user record.",
                    mimetype="text/html",
                    status=500
                )


#   DELETE A COMMENT
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        result = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        userId = resolve_login_token(loginToken)
        commentId = parameters["commentId"]
        print(loginToken)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM comment WHERE userId=? AND commentId=?", [userId, commentId])
            result = cursor.rowcount
            conn.commit()
            print(result)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    "Your comment has been deleted",
                    mimetype = "html/text",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem deleting that comment.",
                    mimetype="text/html",
                    status=500
                )

# COMMENT-LIKES
@app.route('/api/comment-likes', methods=["GET","POST", "DELETE"])
def commentlikes():
    # GET A COMMENT-LIKE
    if request.method == 'GET':
        conn = None
        cursor = None
        result = None
        userId = None
        username = None
        commentlikes = None
        commentId = request.args.get("commentId")
        if commentId == "":
            commentId = None
        print("commentId: ", commentId)
        try:
            conn = connection()
            cursor = conn.cursor()
            if commentId != None:
                cursor.execute("SELECT comment.userId, comment.commentId, user.username FROM user JOIN comment ON user.userId = comment.userId WHERE comment.commentId=?", [commentId])
                likes = cursor.fetchall()
                commentlikes = []
                for like in likes:
                    like = {
                        "commentId" : likes[0][1],
                        "userId" : likes[0][0],
                        "username" : likes[0][2]
                    }
                    commentlikes.append(like)
                print("first Comment likes: ", commentlikes)
            elif (commentId == None):
                cursor.execute("SELECT comment.userId, comment.commentId, user.username FROM user JOIN comment ON user.userId = comment.userId")
                likes = cursor.fetchall()
                print(likes)
                commentlikes = []
                for like in likes:
                    like = {
                        "userId" : likes[0][0],
                        "commentId": likes[0][1],
                        "username" : usernames[0][3]
                    }
                    commentlikes.append(like)
                    print("second Comment likes: ", commentlikes)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                return Response(
                    json.dumps(commentlikes, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
    #POST A COMMENT-LIKE
    elif request.method == 'POST':
        conn = None
        cursor = None
        result = None
        username = None
        parameters = request.get_json()
        loginToken = parameters["loginToken"]
        ClikeId = resolve_login_token(loginToken)
        commentId = parameters["commentId"]
        print(loginToken)
        print(commentId)
        print(ClikeId)
        try:
            conn = connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO comment_like (commentId, ClikeId) VALUES(?, ?)", [commentId, ClikeId])
            conn.commit()
            rowcount = cursor.rowcount
            print(rowcount)
            cursor.execute("SELECT username FROM user WHERE userId=?", [ClikeId])
            username = cursor.fetchone()
            print(username)
        except mariadb.OperationalError:
            return Response("connection problem", mariadb.OperationalError)  
        finally: 
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
                result = {
                    "commentId": commentId,
                    "userId": ClikeId,
                    "username": username,
                }
                return Response(
                    json.dumps(result, default=str),
                    mimetype = "application/json",
                    status=200
                )
            else: 
                return Response(
                    "There was a problem completing the request.",
                    mimetype="text/html",
                    status=500
                )
    # DELETE A COMMENT-LIKE
    elif request.method == 'DELETE':
            conn = None
            cursor = None
            result = None
            parameters = request.get_json()
            loginToken = parameters["loginToken"]
            ClikeId = resolve_login_token(loginToken)
            print(ClikeId)
            print(loginToken)
            commentId = parameters["commentId"]
            print(commentId)
            try:
                conn = connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM comment_like WHERE ClikeId=? AND commentId=?", [ClikeId, commentId])
                result = cursor.rowcount
                print(result)
                conn.commit()
            except mariadb.OperationalError:
                return Response("connection problem", mariadb.OperationalError)  
            finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                    return Response(
                        "Your comment-like has been deleted. ",
                        mimetype = "html/text",
                        status=200
                    )
                else: 
                    return Response(
                        "There was a problem completing the request.",
                        mimetype="text/html",
                        status=500
                    )
