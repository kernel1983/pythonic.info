import os
import hashlib
import time
import datetime
import string
import random
import urlparse
import json
import StringIO

import tornado.web
import tornado.httpclient as httpclient

import markdown2
from PIL import Image
from tornado_ses import EmailHandler
from amazon_ses import EmailMessage

import nomagic
import nomagic.feeds

from setting import conn

from controller.base import BaseHandler


##### mock data API #####
class LoginAPIHandler(BaseHandler):
    def get(self):
        login = self.get_argument("login")
        login_index = conn.get("SELECT * FROM index_login WHERE login = %s", login)
        if login_index:
            self.finish({})
            return
        self.finish({"error":"not exists"})

    def post(self):
        login = self.get_argument("login")
        password = self.get_argument("password")
        user_id, user = nomagic.check_user(login, password)
        if user:
            cookies = {"user_id": user_id}
            self.set_secure_cookie("user", tornado.escape.json_encode(cookies))
            self.finish(cookies)
            return
        raise tornado.web.HTTPError(401, "User not login")

class SignupAPIHandler(BaseHandler, EmailHandler):
    def post(self):
        email = self.get_argument("email")
        token = nomagic.email_invite(email)
        print token

        #send email
        msg = EmailMessage()
        msg.subject = u"Confirm email from Pythonic Info"
        msg.bodyText= u"http://pythonic.info/verify_email?token=%s" % token
        self.send("info@pythonic.info", email, msg)
        self.finish({})

class UserInfoAPIHandler(BaseHandler):
    def get(self):
        user = {}
        if self.current_user:
            user_id = self.current_user["user_id"].encode("utf8")
            user = nomagic._get_entity_by_id(user_id)

        self.finish(user)

    def post(self):
        if self.current_user:
            post_data = dict(zip(self.request.arguments.keys(), [i[0] for i in self.request.arguments.values()]))
            if(set(post_data.keys())-set(['name','title','department','mobile','about'])==set([])):
                #print post_data
                nomagic.update_user(self.current_user["user_id"], post_data)
                self.finish({"result":"success"})
                return
        self.finish({"result":"error"})


class FeedAPIHandler(BaseHandler):
    def get(self):
        self.set_header("Cache-Control", "max-age=0")
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        from_id = self.get_argument("from", None)
        feeds = nomagic.feeds.get_public_feed(item_start_id = from_id)
        users = dict(nomagic._get_entities_by_ids(set([i["user_id"] for i in feeds])))

        self.finish({"users": users, "feeds": feeds})


class ItemAPIHandler(BaseHandler):
    def get_comments(self, comments):
        for comment in comments:
            comment["comments"] = self.get_comments(comment["comments"]) if comment.get("comment_ids") else []
            comment["content"] = markdown2.markdown(comment["content"], safe_mode=True)
        return comments

    def get(self):
        self.set_header("Cache-Control", "max-age=0")
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        entity_id = self.get_argument("id")
        #user_id = self.current_user["user_id"].encode("utf8")
        item, user_ids = nomagic.feeds.get_item_by_id(entity_id)
        item["comments"] = self.get_comments(item["comments"])
        item["content"] = markdown2.markdown(item["content"], safe_mode=True)
        users = dict(nomagic._get_entities_by_ids(user_ids))

        self.finish({"users": users, "item": item})

class PostStatusAPIHandler(BaseHandler):
    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        user_id = self.current_user["user_id"].encode("utf8")
        content = self.get_argument("content").encode("utf8")

        data = {"content": content}
        status_id, status = nomagic.feeds.new_status(user_id, data)

        self.finish(dict(status, id=status_id))

class LikeAPIHandler(BaseHandler):
    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        activity_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")

        likes = nomagic.feeds.like(user_id, activity_id)
        self.finish({"likes": likes, "like_count":len(likes)})

class UnlikeAPIHandler(BaseHandler):
    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        activity_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")

        likes = nomagic.feeds.unlike(user_id, activity_id)
        self.finish({"likes": likes, "like_count":len(likes)})

class PostCommentAPIHandler(BaseHandler):
    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        activity_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")
        content = self.get_argument("content").encode("utf8")

        data = {"content": content}
        comment_ids, new_comment = nomagic.feeds.new_comment(user_id, activity_id, data)

        self.finish({"new_comment":new_comment, "comment_ids":comment_ids, "comment_count":len(comment_ids)})

class ProfileImgAPIHandler(BaseHandler):
    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST, DELETE')

        if self.request.files["upload"][0]["content_type"] in ["image/png", "image/jpeg"]:
            fileName, fileExtension = os.path.splitext(self.request.files["upload"][0]["filename"])
            fileMD5 = hashlib.md5(self.request.files["upload"][0]["body"]).hexdigest()
            with open("static/upload/"+fileMD5+fileExtension, "w") as f:
                f.write(self.request.files["upload"][0]["body"])

            f = StringIO.StringIO(self.request.files["upload"][0]["body"])
            im = Image.open(f)
            im.resize((175, 175)).save("static/upload/"+fileMD5+"_175x175"+fileExtension)
            im.resize((40, 40)).save("static/upload/"+fileMD5+"_40x40"+fileExtension)

            profile_images = {"profile_img_40x40":"/static/upload/"+fileMD5+"_40x40"+fileExtension,
                              "profile_img_175x175":"/static/upload/"+fileMD5+"_175x175"+fileExtension}
            nomagic.update_user(self.current_user["user_id"], profile_images)

            self.finish()
            return
        raise tornado.web.HTTPError(500, "Image file not support")

class FollowAPIHandler(BaseHandler):
    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        user_id = self.current_user["user_id"].encode("utf8")
        friend_ids = self.get_argument("friend_ids").encode("utf8").split(",")
        nomagic.follow_users(user_id, friend_ids)

class UnfollowAPIHandler(BaseHandler):
    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        user_id = self.current_user["user_id"].encode("utf8")
        friend_ids = self.get_argument("friend_ids").encode("utf8").split(",")
        nomagic.unfollow_users(user_id, friend_ids)

class ResendVerifyEmailAPIHandler(BaseHandler):
    def post(self):
        self.verify_code = self.get_argument("verify_code")
