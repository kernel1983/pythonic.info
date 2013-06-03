#!/usr/bin/env python
# -*- coding: utf8 -*-

import time
import datetime
import pickle
import uuid
import binascii
import json

import zlib
#import gzip
import hashlib
import random
import string

import __init__ as nomagic

from setting import settings

from setting import conn
from setting import ring


def email_invite(email):
    """email invite can be used for both self signup and inviting friends to join"""
    # valid email, existing in system?
    # insert into index_invite table
    token = uuid.uuid4().hex
    assert conn.execute_rowcount("INSERT INTO index_invite (email, token) VALUES(%s, %s)", email, token)
    # resend? signup? invite?
    return token

def follow_users(user_id, friend_ids):
    user = nomagic._get_entity_by_id(user_id)
    following = user.get("following", [])
    suggested_friend_ids = user.get("suggested_friend_ids", [])
    changed = False
    for friend_id in friend_ids:
        if friend_id not in following:
            friend = nomagic._get_entity_by_id(friend_id)
            followed = friend.get("followed", [])
            if user_id not in followed:
                followed.append(user_id)
                friend["followed"] = followed
            update_user(friend_id, friend)
            following.append(friend_id)
            changed = True

        if friend_id in suggested_friend_ids:
            suggested_friend_ids.remove(friend_id)
            changed = True

    if changed:
        user["following"] = following
        user["suggested_friend_ids"] = suggested_friend_ids
        update_user(user_id, user)
    #followed = user.get("followed", [])

def unfollow_users(user_id, friend_ids):
    user = nomagic._get_entity_by_id(user_id)
    following = user.get("following", [])
    for friend_id in friend_ids:
        if friend_id in following:
            friend = nomagic._get_entity_by_id(friend_id)
            followed = friend.get("followed", [])
            if user_id in followed:
                followed.remove(user_id)
                friend["followed"] = followed

                update_user(friend_id, friend)
            following.remove(friend_id)

    user["following"] = following
    update_user(user_id, user)


def new_status(user_id, data):
    now = datetime.datetime.now()
    data["type"] = "status"
    data["user_id"] = user_id
    data["datetime"] = now.isoformat()
    data["likes"] = []
    data["comment_ids"] = []
    assert data.get("content")

    new_id = nomagic._new_key()
    assert ring[nomagic._number(new_id)].execute_rowcount("INSERT INTO entities (id, body) VALUES(%s, %s)", new_id, nomagic._pack(data))

    user = nomagic._get_entity_by_id(user_id)
    activity = user.get("activity", [])
    activity.append(new_id)
    user["activity"] = activity
    nomagic._update_entity_by_id(user_id, user)

    posts_in_year_entity_id, posts_in_year = get_posts_entity_by_year(user_id, now.year)
    posts_today = posts_in_year.get(str(now.month), {}).get(str(now.day), [])
    posts_today.append(new_id)
    posts_in_year[str(now.month)][str(now.day)] = posts_today
    nomagic._update_entity_by_id(posts_in_year_entity_id, posts_in_year)

    data["user"] = user
    data["like_count"] = 0
    data["like"] = False
    data["comment_count"] = 0
    data["comments"] = []

    assert conn.execute_rowcount("INSERT INTO index_posts (user_id, entity_id) VALUES(%s, %s)", user_id, new_id)
    return new_id, data


def get_news_feed_by_user_id(user_id, activity_offset=0, activity_start_id=None):
    """
    This part need to rewrite because it doesn't compile all the friends' post
    We need to fix it by using index_posts table
    SELECT * FROM ... WHERE user_id in (...)
    """
    user = nomagic._get_entity_by_id(user_id)
    activity_ids = user.get("activity", []) if user else []
    if user:
        activities = [dict(activity, id=activity_id)
                        for activity_id, activity in nomagic._get_entities_by_ids(activity_ids)]
        return [dict(activity,
                     like_count = len(activity.get("likes", [])),
                     comment_count = len(activity.get("comment_ids", [])),
                     comments = [dict(comment,
                                      like_count = len(comment.get("likes", [])),
                                      id=comment_id)
                                 for comment_id, comment in nomagic._get_entities_by_ids(activity.get("comment_ids", []))])
                     for activity in activities]
    return []

def get_public_news_feed(activity_offset=10, activity_start_id=None):
    if activity_start_id:
        pass
    else:
        posts = conn.query("SELECT * FROM index_posts ORDER BY id DESC LIMIT 0, %s", activity_offset)
    activity_ids = [i["entity_id"] for i in posts]

    if posts:
        activities = [dict(activity, id=activity_id)
                        for activity_id, activity in nomagic._get_entities_by_ids(activity_ids)]
        return [dict(activity,
                     like_count = len(activity.get("likes", [])),
                     comment_count = len(activity.get("comment_ids", [])),
                     comments = [dict(comment,
                                      like_count = len(comment.get("likes", [])),
                                      id=comment_id)
                                 for comment_id, comment in nomagic._get_entities_by_ids(activity.get("comment_ids", []))])
                     for activity in activities]
    return []

def new_comment(user_id, entity_id, data):
    data["type"] = "comment"
    data["likes"] = []
    data["user_id"] = user_id
    data["activity_id"] = entity_id
    data["datetime"] = datetime.datetime.now().isoformat()
    data["comment_ids"] = []
    #content valid
    assert data.get("content")

    new_comment_id = nomagic._new_key()
    assert ring[nomagic._number(new_comment_id)].execute_rowcount("INSERT INTO entities (id, body) VALUES(%s, %s)", new_comment_id, nomagic._pack(data))

    entity = nomagic._get_entity_by_id(entity_id)
    comment_ids = entity.get("comment_ids", [])
    comment_ids.append(new_comment_id)
    entity["comment_ids"] = comment_ids
    nomagic._update_entity_by_id(entity_id, entity)

    return comment_ids, dict(data, id=new_comment_id, like_count=0, like=False, user=nomagic._get_entity_by_id(user_id))

"""
def get_comments(entity_id):
    entity = nomagic._get_entity_by_id(entity_id)
    comment_ids = entity.get("comment_ids", []) if entity else []
    if entity:
        if len(comment_ids) > 1:
            return conn.query("SELECT * FROM entities WHERE id IN %s" % str(tuple(comment_ids)))
        elif len(comment_ids) == 1:
            return conn.query("SELECT * FROM entities WHERE id = %s", comment_ids[0])
    return []
"""

def like(user_id, entity_id):
    entity = nomagic._get_entity_by_id(entity_id)
    likes = entity.get("likes", [])
    if user_id not in likes:
        likes.append(user_id)
        entity["likes"] = likes
        nomagic._update_entity_by_id(entity_id, entity)
    return likes

def unlike(user_id, entity_id):
    entity = nomagic._get_entity_by_id(entity_id)
    likes = entity.get("likes", [])
    if user_id in likes:
        likes.remove(user_id)
        entity["likes"] = likes
        nomagic._update_entity_by_id(entity_id, entity)
    return likes


