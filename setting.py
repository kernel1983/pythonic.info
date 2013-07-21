import os

import json
import tornado.database


settings = {
    #"xsrf_cookies": True,
    "static_path": os.path.join(os.path.dirname(__file__), "static/"),
    "AmazonAccessKeyID": "--------------------",
    "AmazonSecretAccessKey": "----------------------------------------",
    "cookie_secret": "--------------------------------------------",
    "email_sender": "info@pythonic.info",
    "login_url": "/login",
    "debug": True,
}


conn1 = tornado.database.Connection("127.0.0.1", "test1", "root", "")
conn2 = tornado.database.Connection("127.0.0.1", "test2", "root", "")

conn = tornado.database.Connection("127.0.0.1", "test", "root", "")
ring = [conn1, conn2]
