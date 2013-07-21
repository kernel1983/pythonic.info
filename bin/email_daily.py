import sys
import os
import datetime
import time
import pickle
import uuid
import binascii
import json
import zlib

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../vendor')

import tornado.template
import tornado.locale
import amazon_ses

from setting import settings
from setting import conn

import nomagic


def daily(hours):
    now = time.time()
    offset = 0
    post_ids_to_email = set()
    while True:
        index_posts = conn.query("SELECT * FROM index_posts ORDER BY rank DESC LIMIT %s, 100", offset)

        if len(index_posts) == 0:
            break

        post_ids = [post["entity_id"] for post in index_posts]
        for post_id, post in nomagic._get_entities_by_ids(post_ids):
            period = (now - time.mktime(datetime.datetime.strptime(post["datetime"], "%Y-%m-%dT%H:%M:%S.%f").timetuple())) / 3600

            if period <= hours:
                post_ids_to_email.add(post_id)

        offset += 100

    posts_to_email = nomagic._get_entities_by_ids(post_ids_to_email)
    loader = tornado.template.Loader(os.path.dirname(os.path.abspath(__file__)) + "/../template/")

    locale = tornado.locale.get()
    msg = amazon_ses.EmailMessage()
    msg.subject = locale.translate('Pythonic Info Daily').encode("utf-8")
    msg.bodyHtml = loader.load("email_daily.html").generate(posts=posts_to_email, _=locale.translate)

    users_exists = conn.query("SELECT * FROM index_login")
    users_invited = conn.query("SELECT * FROM invite")

    sender = amazon_ses.AmazonSES(settings["AmazonAccessKeyID"], settings["AmazonSecretAccessKey"])
    for email in set([user["login"] for user in users_exists] + [user["email"] for user in users_invited]):
        if "@" in email:
            print email
            sender.sendEmail(settings["email_sender"], email, msg)


if __name__ == '__main__':
    tornado.locale.load_translations(os.path.join(os.path.dirname(__file__) + "/../csv_translations/"))
    tornado.locale.set_default_locale("zh_CN")

    if len(sys.argv) < 2:
        sys.exit()

    hours = float(sys.argv[1])
    print hours

    daily(hours)

