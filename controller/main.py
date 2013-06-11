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

from setting import settings
from setting import conn

import nomagic
import nomagic.auth

from controller.base import *

loader = tornado.template.Loader(os.path.join(os.path.dirname(__file__), "../template/"))


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
            topic["like"] = False
            topic["comment_count"] = 0
            topic["user"] = self.users[topic["user_id"]]

            html_topics.append(self.topic_temp.generate(**topic))

        self.render("../template/html_feed.html", topics=html_topics)


class ItemHandler(BaseHandler):
    topic_temp = loader.load("temp_item_topic.html")
    comment_temp = loader.load("temp_item_comment.html")

    def get_comments(self, comments):
        html_comments = []
        for comment in comments:
            comment["like_count"] = len(comment.get("likes", []))
            comment["like"] = False
            comment["comment_count"] = 0
            if comment.get("comment_ids"):
                comment["comments"] = self.get_comments(comment["comments"])
            else:
                comment["comments"] = []
            comment["user"] = self.users[comment["user_id"]]

            html_comments.append(self.comment_temp.generate(**comment))

        return html_comments

    def get_news_by_id(self, activity_id):
        activity = nomagic._get_entity_by_id(activity_id)
        activity["id"] = activity_id
        comments, user_ids = nomagic.feeds.get_comments(activity)
        self.users = dict(nomagic._get_entities_by_ids(user_ids))

        data = dict(activity,
                    id = activity_id,
                    like_count = len(activity.get("likes", [])),
                    like = False,
                    user = self.users[activity["user_id"]],
                    comment_count = 0, #len(activity.get("comment_ids", [])),
                    comments = self.get_comments(comments),
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
            raise HTTPError(401)
            return

        self.activity_id = self.get_argument("id")
        self.render("../template/html_comment.html")

    def post(self):
        if not self.current_user:
            raise HTTPError(401)
            return

        self.activity_id = self.get_argument("id")
        self.render("/item?id=%s" % self.activity_id)



class CommentHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            raise HTTPError(401)
            return

        self.activity_id = self.get_argument("id")
        self.render("../template/html_comment.html")

    def post(self):
        if not self.current_user:
            raise HTTPError(401)
            return

        self.activity_id = self.get_argument("id")
        self.render("/item?id=%s" % self.activity_id)

