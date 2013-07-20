import sys
import os
import logging
import cgi

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/vendor')

os.chdir(os.path.dirname(os.path.abspath(__file__)))

#import wsgiref.simple_server
#import wsgiref.handlers
#import tornado.wsgi
import tornado.options
import tornado.ioloop
import tornado.web
import tornado.template
import tornado.database
import tornado.auth
import tornado.locale

from setting import settings
from setting import conn

from controller import main
from controller import api
from controller import auth

handlers = [
    (r"/", main.FeedHandler),
    (r"/item", main.ItemHandler),
    (r"/submit", main.SubmitHandler),
    (r"/comment", main.CommentHandler),
    (r"/verify_email", main.VerifyEmailHandler),
    (r"/invite", main.InviteHandler),

    (r"/setting", main.SettingHandler),
    (r"/login", main.LoginHandler),
    (r"/logout", main.LogoutHandler),

    (r"/api/login", api.LoginAPIHandler),
    (r"/api/signup", api.SignupAPIHandler),
    (r"/api/user_info", api.UserInfoAPIHandler),
    (r"/api/get_feed", api.FeedAPIHandler),
    (r"/api/get_item", api.ItemAPIHandler),
    (r"/api/profile_img", api.ProfileImgAPIHandler),

    (r"/api/like", api.LikeAPIHandler),
    (r"/api/unlike", api.UnlikeAPIHandler),
    (r"/api/follow", api.FollowAPIHandler),
    (r"/api/unfollow", api.UnfollowAPIHandler),

    (r"/api/post_status", api.PostStatusAPIHandler),
    (r"/api/post_comment", api.PostCommentAPIHandler),

    (r"/auth/google", auth.GoogleHandler),
    (r"/auth/logout", auth.LogoutHandler),

    #(r"/()", tornado.web.StaticFileHandler, dict(path=settings['static_path']+'/index.html')),
    #(r"/(.*)", tornado.web.StaticFileHandler, dict(path=settings['static_path'], default_filename='index.html')),
]


if __name__ == "__main__":
    tornado.locale.load_translations(os.path.join(os.path.dirname(__file__), "csv_translations"))
    tornado.locale.set_default_locale("zh_CN")
    tornado.options.define("port", default=8000, help="Run server on a specific port", type=int)
    tornado.options.parse_command_line()
    application = tornado.web.Application(handlers, **settings)
    application.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()

