import urllib

import tornado.httpclient as httpclient

from amazon_ses import AmazonSES


class EmailHandler(AmazonSES):
    def send(self, from_email, user_email, user_msg):
        AmazonSES.__init__(self, self.settings["AmazonAccessKeyID"], self.settings["AmazonSecretAccessKey"])
        self.sendEmail(from_email, user_email, user_msg)

    def handle_email(self, response):
        pass

    def _performAction(self, actionName, params=None):
        if not params:
            params = {}
        params['Action'] = actionName
        params = urllib.urlencode(params)

        conn = httpclient.AsyncHTTPClient()
        req = httpclient.HTTPRequest("https://email.us-east-1.amazonaws.com/", "POST", self._getHeaders(), params)
        conn.fetch(req, self.handle_email)
