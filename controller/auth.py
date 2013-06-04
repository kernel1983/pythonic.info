import sys
import os
import logging
import time
import cgi
import string
import random
import json

import tornado.options
import tornado.ioloop
import tornado.web

import tornado.template
import tornado.database
import tornado.auth

import nomagic

from setting import settings
from setting import conn

from main import BaseHandler


class GoogleHandler(tornado.web.RequestHandler,
                    #EmailHandler,
                    tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.redirect_url = self.get_argument("next", "/")
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()

    def _on_auth(self, google_user):
        if not google_user:
            raise tornado.web.HTTPError(500, "Google auth failed")

        current_user = conn.get("SELECT * FROM index_login WHERE login = %s", google_user["email"])

        if current_user is None:
            user_id, user = nomagic.create_user({"email":google_user["email"], "name":google_user["name"], "google": google_user})

        else:
            user_id = current_user["entity_id"]
            user = nomagic._get_entity_by_id(user_id)
            if "google" not in user:
                raise tornado.web.HTTPError(500, "Can not login with Google")

        self.set_secure_cookie("user", tornado.escape.json_encode({"user_id": user_id}))

        self.redirect(self.redirect_url)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        #self.redirect("https://accounts.google.com/Logout")

