
import unittest
import random
import hashlib

import nomagic
import nomagic.auth
import nomagic.feeds
import nomagic.friends

from setting import conn
from setting import ring

class TestNoMagicFunctions(unittest.TestCase):

    def setUp(self):
        #pass
        self.user_id = nomagic.auth.get_user_id_by_login("kernel1983@gmail.com")

    def tearDown(self):
        pass

    def _test_invite(self):
        nomagic.auth.email_invite("kernel1983+%s@gmail.com"% str(random.randint(100000,1000000)))

    def test_new_user(self):
        try:
            user1 = {
                "name": "kernel1983@gmail.com",
                "email": "kernel1983@gmail.com",
                "password": "1234",
                "email_verified": False
            }
            new_user_id, user1 = nomagic.auth.create_user(user1)

            #nomagic.auth.update_user(new_user_id, user)
        except:
            user_id, user1 = nomagic.auth.check_user(user1["email"], user1["password"])
            assert user1

        user2 = {
            "name": "kernel1983+%s@gmail.com"% str(random.randint(100000,1000000)),
            "email": "kernel1983+%s@gmail.com"% str(random.randint(100000,1000000)),
            "password": "1234",
            "email_verified": False
        }
        new_user_id, user2 = nomagic.auth.create_user(user2)

        # create password 1234
        #password = hashlib.sha1("1234"+user["salt"]).hexdigest()
        #user["password"] = password

        #print user["email"]

        #nomagic.auth.update_user(new_user_id, user)

        nomagic.friends.follow_users(self.user_id, [new_user_id])

    def test_new_status(self):
        #old_activities = nomagic.feeds.get_news_feed_by_user_id(self.user_id)
        #for i in old_activities:
        #    nomagic.feeds.unlike(self.user_id, i["id"])

        #print old_activities
        data = {"title":"mock title %s"%str(random.randint(100,1000000)), "user_id": self.user_id}

        self.status_id, status = nomagic.feeds.new_status(self.user_id, data)
        nomagic.feeds.like(self.user_id, self.status_id)

        #new_activities = nomagic.feeds.get_news_feed_by_user_id(self.user_id)
        #print new_activities
        #assert len(new_activities) - len(old_activities) == 1

        #old_comments = nomagic.get_comments(self.status_id)

        data = {"content": "test"}
        comment_ids, new_comment = nomagic.feeds.new_comment(self.user_id, self.status_id, data)
        #new_comments = nomagic.feeds.get_comments(self.status_id)
        #assert len(new_comments) - len(old_comments) == 1

        comment_ids, new_comment = nomagic.feeds.new_comment(self.user_id, new_comment["id"], data)
        comment_ids, new_comment = nomagic.feeds.new_comment(self.user_id, new_comment["id"], data)

    """
    def _test_new_picture(self):
        data = {"content":"mock content %s"%str(random.randint(100,1000000)), "user_id": self.user_id}
        status = {
             "content": "This is the content",
             "user_id": self.user_id
        }

        self.status_id, status = nomagic.feeds.new_status(self.user_id, data)
        nomagic.feeds.like(self.user_id, self.status_id)

    def test_follow(self):

        #user = {"email": "abc%s@abc.com"% str(random.randint(100,1000000))}
        #user_id = nomagic.auth.create_user(user)

        #nomagic.auth.follow_user
        pass

    def test_new_link(self):
        pass

    def test_new_video(self):
        pass

    def test_like(self):
        pass

    def test_new_(self):
        pass
    """

if __name__ == '__main__':
    #unittest.main(verbosity=2)
    unittest.main()
    conn.close()
    [i.close() for i in ring]

