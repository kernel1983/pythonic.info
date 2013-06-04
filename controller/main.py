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
    def get(self):
        if self.current_user:
            self.user_id = self.current_user.get("user_id", u"").encode("utf8")

        self.render("../template/feed.html")

class ItemHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.user_id = self.current_user.get("user_id", u"").encode("utf8")

        self.activity_id = self.get_argument("id")
        self.render("../template/item.html")
