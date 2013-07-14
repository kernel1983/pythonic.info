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

from setting import conn
import auth

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
            auth.update_user(friend_id, friend)
            following.append(friend_id)
            changed = True

        if friend_id in suggested_friend_ids:
            suggested_friend_ids.remove(friend_id)
            changed = True

    if changed:
        user["following"] = following
        user["suggested_friend_ids"] = suggested_friend_ids
        auth.update_user(user_id, user)
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

                auth.update_user(friend_id, friend)
            following.remove(friend_id)

    user["following"] = following
    auth.update_user(user_id, user)


def new_status(user_id, data):
    now = datetime.datetime.now()
    data["type"] = "status"
    data["user_id"] = user_id
    data["datetime"] = now.isoformat()
    data["likes"] = []
    data["comment_ids"] = []
    assert data.get("title")

    new_id = nomagic._new_key()
    assert nomagic._node(new_id).execute_rowcount("INSERT INTO entities (id, body) VALUES(%s, %s)", new_id, nomagic._pack(data))

    user = nomagic._get_entity_by_id(user_id)
    activity = user.get("activity", [])
    activity.append(new_id)
    user["activity"] = activity
    nomagic._update_entity_by_id(user_id, user)

    data["user"] = user
    data["like_count"] = 0
    data["like"] = False
    data["comment_count"] = 0

    assert conn.execute_rowcount("INSERT INTO index_posts (user_id, entity_id) VALUES(%s, %s)", user_id, new_id)
    return new_id, data


def get_public_feed(item_offset=10, item_start_id=None):
    if item_start_id:
        last_post = conn.get("SELECT * FROM index_posts WHERE entity_id = %s", item_start_id)
        posts = conn.query("SELECT * FROM index_posts WHERE rank < %s ORDER BY rank DESC LIMIT 0, %s", last_post["rank"], item_offset)
    else:
        posts = conn.query("SELECT * FROM index_posts ORDER BY rank DESC LIMIT 0, %s", item_offset)
    item_ids = [i["entity_id"] for i in posts]

    if posts:
        items = [dict(item, id=item_id)
                        for item_id, item in nomagic._get_entities_by_ids(item_ids)]
        return [dict(item,
                     like_count = len(item.get("likes", [])),
                     comment_count = len(item.get("comment_ids", [])),
                     url = item.get("url"),
                     ) for item in items]
    return []

def get_item_by_id(item_id):
    item = nomagic._get_entity_by_id(item_id)
    comments, user_ids = get_comments(item)

    return dict(item,
                id = item_id,
                like_count = len(item.get("likes", [])),
                like = False,
                url = item.get("url"),
                comment_count = 0, #len(activity.get("comment_ids", [])),
                comments = comments), user_ids


def new_comment(user_id, entity_id, data):
    entity = nomagic._get_entity_by_id(entity_id)

    data["type"] = "comment"
    data["likes"] = []
    data["user_id"] = user_id
    data["activity_id"] = entity_id
    data["datetime"] = datetime.datetime.now().isoformat()
    data["comment_ids"] = []
    if entity["type"] == "comment":
        data["activity_id"] = entity.get("activity_id")
    else:
        data["activity_id"] = entity_id
    #content valid
    assert data.get("content")

    new_comment_id = nomagic._new_key()
    assert nomagic._node(new_comment_id).execute_rowcount("INSERT INTO entities (id, body) VALUES(%s, %s)", new_comment_id, nomagic._pack(data))

    comment_ids = entity.get("comment_ids", [])
    comment_ids.append(new_comment_id)
    entity["comment_ids"] = comment_ids
    nomagic._update_entity_by_id(entity_id, entity)

    return comment_ids, dict(data, id=new_comment_id, like_count=0, like=False, user=nomagic._get_entity_by_id(user_id))


def get_comments(entity, user_ids = set()):
    assert "comment_ids" in entity
    assert "comments" not in entity
    entity_comments = entity.get("comments", [])
    for comment_id, comment in nomagic._get_entities_by_ids(entity.get("comment_ids", [])):
        comment["id"] = comment_id
        comment["like_count"] = len(comment.get("likes", [])),
        comment["comment_count"] = 0, #len(activity.get("comment_ids", [])),
        user_ids.add(comment["user_id"])
        if comment.get("comment_ids"):
            get_comments(comment, user_ids)
        entity_comments.append(comment)

    entity["comments"] = entity_comments
    return entity_comments, user_ids

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


