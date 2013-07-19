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

from setting import settings
from setting import conn

import nomagic


def rank(points, period): return int( (points + 1) /  ( (period + 2) ** 1.8) * 1000000000 )

def ranking():
    now = time.time()
    offset = 0
    while True:
        index_posts = conn.query("SELECT * FROM index_posts ORDER BY rank DESC LIMIT %s, 100", offset)

        if len(index_posts) == 0:
            break

        post_ids = [post["entity_id"] for post in index_posts]
        for post_id, post in nomagic._get_entities_by_ids(post_ids):
            period = (now - time.mktime(datetime.datetime.strptime(post["datetime"], "%Y-%m-%dT%H:%M:%S.%f").timetuple())) / 3600
            points = len(post["likes"])
            post_rank = rank(points, period)

            conn.execute("UPDATE index_posts SET rank = %s WHERE entity_id = %s", post_rank, post_id)

        offset += 100

if __name__ == '__main__':
    #print rank(0, 0)
    #print rank(3000, 0)
    ranking()

