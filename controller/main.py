import sys
import os
import logging
import cgi
import json
import random
import string
import urllib

import tornado.options
import tornado.ioloop
import tornado.web

import tornado.template
import tornado.database
import tornado.auth
import tornado.locale

import markdown2
from tornado_ses import EmailHandler
from amazon_ses import EmailMessage

from setting import settings
from setting import conn

import nomagic
import nomagic.auth
import nomagic.feeds

from controller.base import *

loader = tornado.template.Loader(os.path.join(os.path.dirname(__file__), "../template/"))

class SettingHandler(BaseHandler):
    def get(self):
        self.set_header("Cache-Control", "max-age=0")
        if not self.current_user:
            self.redirect("/login")
            return

        user_id = self.current_user["user_id"].encode("utf8")
        self.user = nomagic._get_entity_by_id(user_id)
        self.render('../template/setting.html')

    def post(self):
        if self.current_user:
            user_id = self.current_user["user_id"].encode("utf8")
            self.user = nomagic._get_entity_by_id(user_id)
            post_data = {}

            name = self.get_argument("name", None)
            if name:
                post_data["name"] = name

            receive_daily_email = bool(self.get_argument("receive_daily_email", False))
            if self.user.get("receive_daily_email", True) != receive_daily_email:
                print receive_daily_email
                post_data["receive_daily_email"] = receive_daily_email
            if post_data:
                nomagic.auth.update_user(user_id, post_data)

            password0 = self.get_argument("password0", None)
            password1 = self.get_argument("password1", None)
            password2 = self.get_argument("password2", None)
            if password0 is not None and password1 is not None and password1 == password2:
                post_data = {}
                post_data["password0"] = password0
                post_data["password1"] = password1
                nomagic.auth.update_user(user_id, post_data)
                self.redirect("/setting?status=password_updated")
                return

        self.redirect("/setting")


class LoginHandler(BaseHandler, EmailHandler):
    def get(self):
        self.email = self.get_argument("email", u"")
        self.invite_code = self.get_argument("invite_code", u"")
        self.render('../template/login.html')

    def post(self):
        login = self.get_argument("login", None)
        password = self.get_argument("password", None)

        invite_code = self.get_argument("invite_code", None)
        email = self.get_argument("email", None)
        name = self.get_argument("name", None)
        password1 = self.get_argument("password1", None)
        password2 = self.get_argument("password2", None)

        if login and password:
            user_id, user = nomagic.auth.check_user(login, password)
            if user_id:
                self.set_secure_cookie("user", tornado.escape.json_encode({"user_id": user_id}))
                self.redirect("/?status=login")
                return

        elif email and name and password1 and password2 and password1 == password2 and invite_code:
            invited = conn.get("SELECT * FROM invite WHERE code = %s", invite_code)
            if not invited:
                self.redirect("/login?status=need_invite_code")
                return

            data = {"email": email, "name": name, "password": password1}
            try:
                user_id, user = nomagic.auth.create_user(data)

                self.set_secure_cookie("user", tornado.escape.json_encode({"user_id": user_id}))

                email_verify_code = ''.join(random.choice(string.digits+string.letters) for x in range(14))
                result = nomagic.auth.update_user(user_id, {"email_verified": False, "email_verify_code": email_verify_code})

                #send verify email here
                msg = EmailMessage()
                msg.subject = "Confirm Email from Pythonic Info"
                msg.bodyText = "http://pythonic.info/verify_email?user_id=%s&verify_code=%s" % (user_id, email_verify_code)
                self.send("info@pythonic.info", str(email), msg)
                print "url:", msg.bodyText

                self.redirect("/?status=created")
                return
            except:
                pass

        self.redirect("/login?status=error")


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.render("../template/logout.html")


class FeedHandler(BaseHandler):
    topic_temp = loader.load("temp_feed_topic.html")

    def get(self):
        self.user_id = ""
        if self.current_user:
            self.user_id = self.current_user.get("user_id", u"").encode("utf8")

        self.from_id = self.get_argument("from", None)
        feeds = nomagic.feeds.get_public_feed(item_start_id = self.from_id)
        self.users = dict(nomagic._get_entities_by_ids(set([i["user_id"] for i in feeds])))

        self.more_id = None
        html_topics = []
        for topic in feeds:
            topic["like_count"] = len(topic.get("likes", []))
            topic["like"] = self.user_id in set(topic.get("likes", [])) if self.current_user else False
            topic["comment_count"] = 0
            topic["user"] = self.users[topic["user_id"]]
            topic["url"] = topic.get("url_cn") if topic.get("url_cn") else topic.get("url_en")
            topic["handler"] = self
            topic["_"] = self.locale.translate
            self.more_id = topic["id"]

            html_topics.append(self.topic_temp.generate(**topic))

        self.set_header("Cache-Control", "max-age=900")
        self.render("../template/html_feed.html", topics=html_topics)


class ItemHandler(BaseHandler):
    topic_temp = loader.load("temp_item_topic.html")
    comment_temp = loader.load("temp_item_comment.html")

    def get_comments(self, comments):
        html_comments = []
        for comment in comments:
            comment["like_count"] = len(comment.get("likes", []))
            comment["like"] = self.user_id in set(comment.get("likes", [])) if self.current_user else False
            comment["comment_count"] = 0
            comment["comments"] = self.get_comments(comment["comments"]) if comment.get("comment_ids") else []
            comment["user"] = self.users[comment["user_id"]]
            comment["content"] = markdown2.markdown(comment["content"], safe_mode=True)
            comment["_"] = self.locale.translate

            html_comments.append(self.comment_temp.generate(**comment))

        return html_comments

    def get_item_by_id(self, item_id):
        item = nomagic._get_entity_by_id(item_id)
        comments, user_ids = nomagic.feeds.get_comments(item)
        user_ids.add(item["user_id"])
        self.users = dict(nomagic._get_entities_by_ids(user_ids))
        url = item.get("url_cn") if item.get("url_cn") else item.get("url_en")
        #url = url if url else "/item?id=%s" % item.get("id")

        data = dict(item,
                    id = item_id,
                    like_count = len(item.get("likes", [])),
                    like = self.user_id in set(item.get("likes", [])) if self.current_user else False,
                    user = self.users[item["user_id"]],
                    comment_count = 0, #len(item.get("comment_ids", [])),
                    comments = self.get_comments(comments),
                    url = url,
                    content = markdown2.markdown(item["content"], safe_mode=True),
                    _ = self.locale.translate,
                    handler = self)

        return self.topic_temp.generate(**data)

    def get(self):
        self.user_id = ""
        if self.current_user:
            self.user_id = self.current_user.get("user_id", u"").encode("utf8")

        self.item_id = self.get_argument("id")
        content = self.get_item_by_id(self.item_id)
        self.set_header("Cache-Control", "max-age=3600")
        self.render("../template/html_item.html", content=content)


class SubmitHandler(BaseHandler):
    def get(self):
        self.set_header("Cache-Control", "max-age=0")
        if not self.current_user:
            self.redirect("/login")
            return

        self.title = self.get_argument("title", "")
        self.url_cn = self.get_argument("url", "")
        self.url_en = ""
        self.content = ""

        user_id = self.current_user["user_id"].encode("utf8")
        self.user = nomagic._get_entity_by_id(user_id)
        self.render("../template/html_submit.html")

    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return

        self.title = self.get_argument("title")
        self.url_cn = self.get_argument("url_cn", "")
        self.url_en = self.get_argument("url_en", "")
        self.content = self.get_argument("content", "")
        self.user_id = self.current_user.get("user_id", u"").encode("utf8")

        if (self.url_en or self.url_cn) or self.content:
            data = {
                "title": self.title,
                "content": self.content,
                "url_en": self.url_en, "url_cn": self.url_cn,
                "user_id": self.user_id}
            self.status_id, status = nomagic.feeds.new_status(self.user_id, data)
            self.redirect("/")
        else:
            self.redirect("/submit")

class CommentHandler(BaseHandler):
    def get(self):
        self.set_header("Cache-Control", "max-age=0")
        if not self.current_user:
            self.redirect("/login")
            return

        comment_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")
        parent = nomagic._get_entity_by_id(comment_id)
        assert parent["type"] in ["comment", "status"]
        parent["like"] = user_id in parent["likes"]
        parent["like_count"] = len(parent["likes"])
        parent["content"] = markdown2.markdown(parent["content"], safe_mode=True)
        parent["edit_content"] = ""

        parent["user"] = nomagic._get_entity_by_id(user_id)
        self.render("../template/html_comment.html", **parent)

    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return

        comment_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")
        content = self.get_argument("content").encode("utf8")

        data = {"content": content}
        comment_ids, new_comment = nomagic.feeds.new_comment(user_id, comment_id, data)

        self.redirect("/item?id=%s" % new_comment.get("activity_id", ""))


class EditItemHandler(BaseHandler):
    def get(self):
        self.set_header("Cache-Control", "max-age=0")
        if not self.current_user:
            self.redirect("/login")
            return

        user_id = self.current_user["user_id"].encode("utf8")
        self.item_id = self.get_argument("id")
        item = nomagic._get_entity_by_id(self.item_id)
        if item['user_id'] != user_id:
            raise tornado.web.HTTPError(401, "Not allow to edit")
            return

        self.title = item["title"]
        self.url_cn = item["url_cn"]
        self.url_en = item["url_en"]
        self.content = item["content"]

        self.user = nomagic._get_entity_by_id(user_id)
        self.render("../template/html_submit.html")

    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return

        self.title = self.get_argument("title")
        self.url_cn = self.get_argument("url_cn", "")
        self.url_en = self.get_argument("url_en", "")
        self.content = self.get_argument("content", "")
        self.item_id = self.get_argument("id")
        self.user_id = self.current_user.get("user_id", u"").encode("utf8")

        if (self.url_en or self.url_cn) or self.content:
            data = {
                "title": self.title,
                "content": self.content,
                "url_en": self.url_en, "url_cn": self.url_cn,
            }
            entity = nomagic._get_entity_by_id(self.item_id)
            entity.update(data)
            nomagic._update_entity_by_id(self.item_id, entity)
            self.redirect("/item?id=%s" % self.item_id)
        else:
            self.redirect("/edit_item?id=%s" % self.item_id)

class EditCommentHandler(BaseHandler):
    def get(self):
        self.set_header("Cache-Control", "max-age=0")
        if not self.current_user:
            self.redirect("/login")
            return

        comment_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")
        parent = nomagic._get_entity_by_id(comment_id)
        if parent['user_id'] != user_id:
            raise tornado.web.HTTPError(401, "Not allow to edit")
            return

        assert parent["type"] in ["comment", "status"]
        parent["like"] = user_id in parent["likes"]
        parent["like_count"] = len(parent["likes"])
        parent["edit_content"] = parent["content"]
        parent["content"] = markdown2.markdown(parent["content"], safe_mode=True)

        parent["user"] = nomagic._get_entity_by_id(user_id)
        self.render("../template/html_comment.html", **parent)

    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return

        comment_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")
        content = self.get_argument("content").encode("utf8")

        data = {"content": content}
        entity = nomagic._get_entity_by_id(comment_id)
        entity.update(data)
        nomagic._update_entity_by_id(comment_id, entity)

        self.redirect("/edit_comment?id=%s" % comment_id)


class VerifyEmailHandler(BaseHandler):
    def get(self):
        user_id = self.get_argument("user_id").encode("utf8")
        email_verify_code = self.get_argument("verify_code")
        self.user = nomagic._get_entity_by_id(user_id)

        self.verified = False
        if self.user.get("email_verify_code") == email_verify_code:
            result = nomagic.auth.update_user(user_id, {"email_verified": True})
            self.verified = True

        self.set_header("Cache-Control", "max-age=0")
        #self.write("done! " + str(self.verified))
        self.render('../template/verify_email.html')


class InviteHandler(BaseHandler, EmailHandler):
    def get(self):
        self.set_header("Cache-Control", "max-age=0")
        if not self.current_user:
            self.redirect("/login")
            return

        self.render('../template/invite.html')

    def post(self):
        if not self.current_user:
            self.redirect("/login")
            return

        email = self.get_argument("email")

        user_exist = conn.get("SELECT * FROM index_login WHERE login = %s", email)
        invited = conn.get("SELECT * FROM invite WHERE email = %s", email)
        if user_exist or invited:
            self.redirect("/invite?status=exists")
            return

        #send email
        invite_code = ''.join(random.choice(string.digits+string.letters) for x in range(14))
        conn.execute("INSERT INTO invite (email, code) VALUES(%s, %s)", email, invite_code)

        self.email = urllib.quote(email)
        self.invite_code = invite_code
        msg = EmailMessage()
        msg.subject = "Invite from Pythonic Info"
        msg.bodyHtml = self.render_string("../template/email_invite.html")
        self.send(settings["email_sender"], str(email), msg)
        print "url:", msg.bodyText

        self.redirect("/invite?status=success")
