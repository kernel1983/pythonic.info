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

from controller.base import *


class LoginHandler(BaseHandler):
    def get(self):
        self.render('../templates/login.html')

class SignupHandler(BaseHandler):
    def get(self):
        self.render('../templates/signup.html')


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/login")


class FeedHandler(BaseHandler):
    topic_temp = tornado.template.Template("""
    <li id="feed-{{ id }}" class="topic">
        <p class="black">{{ content }}</p>
        <div class="gray">
            <a class="unlike {{ "" if like else "hide" }}" id="unlike-{{ id }}"><i class="icon icon-thumbs-down"></i></a>
            <a class="like {{ "hide" if like else "" }}" id="like-{{ id }}"><i class="icon icon-thumbs-up"></i></a>
            <a class="" href="#"> <span id="like-count-{{ id }}">{{ like_count }}</span> Likes</a>
            by <a href="#" class="username">{{ user["name"] }}</a> <abbr class="timeago postTime" title="{{ datetime }}"></abbr>
            <a class="linkSep">|</a> <a class="reply" id="reply-{{ id }}" href="/item?id={{ id }}">discuss</a>
        </div>
    </li>
""")

    def get(self):
        if not self.current_user:
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
            return

        self.user_id = self.current_user.get("user_id", u"").encode("utf8")
        self.render("../template/feed.html")


class ItemHandler(BaseHandler):
    topic_temp = tornado.template.Template("""
    <li id="feed-{{ id }}" class="topic">
        <p class="black">{{ content }}</p>
        <div class="gray">
            <a class="unlike {{ "" if like else "hide" }}" id="unlike-{{ id }}"><i class="icon icon-thumbs-down"></i></a>
            <a class="like {{ "hide" if like else "" }}" id="like-{{ id }}"><i class="icon icon-thumbs-up"></i></a>
            <a class="" href="#"> <span id="like-count-{{ id }}">{{ like_count }}</span> Likes</a>
            by <a href="#" class="username">{{ user["name"] }}</a> <abbr class="timeago postTime" title="{{ datetime }}"></abbr>
        </div>
        {% for comment in comments %}
            {% raw comment %}
        {% end for %}
    </li>
""")

    comment_temp = tornado.template.Template("""
        <div id="feed-{{ id }}" class="comment">
        <div class="gray">
            <a class="unlike {{ "" if like else "hide" }}" id="unlike-{{ id }}"><i class="icon icon-thumbs-down"></i></a>
            <a class="like {{ "hide" if like else "" }}" id="like-{{ id }}"><i class="icon icon-thumbs-up"></i></a>
            <span id="like-count-{{ id }}">{{ like_count }}</span> Likes by <a href="#" class="username">{{ user["name"] }}</a> <abbr class="timeago postTime" title="{{ datetime }}"></abbr>
        </div>
        <p class="black">{{ content }}</p>
        <div class="gray">
            <a class="reply" id="reply-{{ id }}">Reply</a>
        </div>
        {% for comment in comments %}
            {% raw comment %}
        {% end for %}
    </div>
""")

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
                    comments = self.get_comments(comments))

        return self.topic_temp.generate(**data)

    def get(self):
        self.activity_id = self.get_argument("id")
        if not self.current_user:
            activity_id = self.get_argument("id")
            news_feed, user_ids = nomagic.feeds.get_news_by_id(activity_id)

            content = self.get_news_by_id(self.activity_id)
            self.render("../template/html_item.html", content=content)
            return

        self.user_id = self.current_user.get("user_id", u"").encode("utf8")
        self.render("../template/item.html")

