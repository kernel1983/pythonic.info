import sys
import datetime
import time
import pickle
import uuid
import binascii
import json
import zlib

sys.path.append(".")
sys.path.append("..")

from setting import settings
from setting import conn
#from setting import ring

import nomagic
import nomagic.feeds


def get_comments(comments):
    comment_ids = []
    for comment in comments:
        assert comment.get("type") == "comment"
        #comment["like_count"] = len(comment.get("likes", []))
        #comment["like"] = self.user_id in set(comment.get("likes", [])) if self.current_user else False
        #comment["comment_count"] = 0
        #print comment["comments"] if comment.get("comments") else []
        comment_ids.append(comment["id"])
        comment_ids.extend(get_comments(comment["comments"]) if comment.get("comments") else [])

    return comment_ids

if len(sys.argv) < 2:
    sys.exit()

print sys.argv[1]
activity_id = sys.argv[1]

activity = nomagic._get_entity_by_id(activity_id)
print activity
assert activity.get("type") == "status"

comments, user_ids = nomagic.feeds.get_comments(activity)
comment_ids = get_comments(comments)
print comment_ids

# delete comment_ids
for comment_id in comment_ids:
    nomagic._node(comment_id).execute_rowcount("DELETE FROM entities WHERE id = %s", comment_id)

# delete activity_id
nomagic._node(activity_id).execute_rowcount("DELETE FROM entities WHERE id = %s", activity_id)

conn.execute_rowcount("DELETE FROM index_posts WHERE entity_id = %s", activity_id)
