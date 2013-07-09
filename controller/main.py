import sys
import os
import logging
import cgi
import json

import tornado.options
import tornado.ioloop
import tornado.web

import tornado.template
import tornado.database
import tornado.auth
import tornado.locale

import markdown2

from setting import settings
from setting import conn

import nomagic
import nomagic.auth
import nomagic.feeds

from controller.base import *

loader = tornado.template.Loader(os.path.join(os.path.dirname(__file__), "../template/"))

class SettingHandler(BaseHandler):
    def get(self):
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

            name = self.get_argument("name", None)
            if name:
                post_data = {}
                post_data["name"] = name
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


class LoginHandler(BaseHandler):
    def get(self):
        self.render('../template/login.html')

    def post(self):
        login = self.get_argument("login", None)
        password = self.get_argument("password", None)

        email = self.get_argument("email", None)
        password1 = self.get_argument("password1", None)
        password2 = self.get_argument("password2", None)

        if login and password:
            user_id, user = nomagic.auth.check_user(login, password)
            if user_id:
                self.set_secure_cookie("user", tornado.escape.json_encode({"user_id": user_id}))
                self.redirect("/?status=login")
                return

        elif email and password1 and password2 and password1 == password2:
            data = {"email": email, "password": password1}
            try:
                user_id, user = nomagic.auth.create_user(data)

                self.set_secure_cookie("user", tornado.escape.json_encode({"user_id": user_id}))
                self.redirect("/?status=created")
                return
            except:
                pass

        self.redirect("/login?status=error")


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")


class FeedHandler(BaseHandler):
    topic_temp = loader.load("temp_feed_topic.html")

    def get(self):
        if self.current_user:
            self.user_id = self.current_user.get("user_id", u"").encode("utf8")

        news_feeds = nomagic.feeds.get_public_news_feed()
        self.users = dict(nomagic._get_entities_by_ids(set([i["user_id"] for i in news_feeds])))

        html_topics = []
        for topic in news_feeds:
            topic["like_count"] = len(topic.get("likes", []))
            topic["like"] = self.user_id in set(topic.get("likes", [])) if self.current_user else False
            topic["comment_count"] = 0
            topic["user"] = self.users[topic["user_id"]]
            topic["url"] = topic.get("url_cn") if topic.get("url_cn") else topic.get("url_en")
            topic["handler"] = self
            topic["_"] = self.locale.translate

            html_topics.append(self.topic_temp.generate(**topic))

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

    def get_news_by_id(self, activity_id):
        activity = nomagic._get_entity_by_id(activity_id)
        activity["id"] = activity_id
        comments, user_ids = nomagic.feeds.get_comments(activity)
        user_ids.add(activity["user_id"])
        self.users = dict(nomagic._get_entities_by_ids(user_ids))
        url = activity.get("url_cn") if activity.get("url_cn") else activity.get("url_en")
        #url = url if url else "/item?id=%s" % activity.get("id")

        data = dict(activity,
                    id = activity_id,
                    like_count = len(activity.get("likes", [])),
                    like = self.user_id in set(activity.get("likes", [])) if self.current_user else False,
                    user = self.users[activity["user_id"]],
                    comment_count = 0, #len(activity.get("comment_ids", [])),
                    comments = self.get_comments(comments),
                    url = url,
                    content = markdown2.markdown(activity["content"], safe_mode=True),
                    _ = self.locale.translate,
                    handler = self)

        return self.topic_temp.generate(**data)

    def get(self):
        if self.current_user:
            self.user_id = self.current_user.get("user_id", u"").encode("utf8")

        self.activity_id = self.get_argument("id")
        news_feed, user_ids = nomagic.feeds.get_news_by_id(self.activity_id)

        content = self.get_news_by_id(self.activity_id)
        self.render("../template/html_item.html", content=content)


class SubmitHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return

        user_id = self.current_user["user_id"].encode("utf8")
        self.user = nomagic._get_entity_by_id(user_id)
        self.render("../template/html_submit.html")

    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
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
        if not self.current_user:
            self.redirect("/login")
            return

        self.activity_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")
        parent = nomagic._get_entity_by_id(self.activity_id)
        assert parent["type"] in ["comment", "status"]
        parent["like"] = user_id in parent["likes"]
        parent["like_count"] = len(parent["likes"])

        parent["user"] = nomagic._get_entity_by_id(user_id)
        self.render("../template/html_comment.html", **parent)


    def post(self):
        if not self.current_user:
            raise tornado.web.HTTPError(401, "User not login")
            return

        self.activity_id = self.get_argument("id").encode("utf8")
        user_id = self.current_user["user_id"].encode("utf8")
        content = self.get_argument("content").encode("utf8")

        data = {"content": content}
        comment_ids, new_comment = nomagic.feeds.new_comment(user_id, self.activity_id, data)

        self.redirect("/item?id=%s" % new_comment.get("activity_id", ""))
