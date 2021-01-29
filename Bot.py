import json
import atexit
import fbchat


class Bot:
    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd
        self.cookies_path = "{}_cookies.json".format(username.split('@')[0])
        self.session = None
        self.uId = None

    async def initialize_session(self):
        self.session = await self.get_session()
        self.uId = self.session.user.id
        print("Session initialized")

    async def get_session(self):
        cookies = self.load_cookies(self.cookies_path)
        session = await self.load_session(cookies)
        if not session:
            session = await fbchat.Session.login(self.username, self.passwd)

        atexit.register(lambda: self.save_cookies(self.cookies_path, session.get_cookies()))
        return session

    def load_cookies(self, filename):
        try:
            with open(filename) as f:
                return json.load(f)
        except FileNotFoundError:
            return  # No cookies yet

    def save_cookies(self, filename, cookies):
        with open(filename, 'w') as f:
            json.dump(cookies, f)

    async def load_session(self, cookies):
        if not cookies:
            return
        try:
            return await fbchat.Session.from_cookies(cookies)
        except fbchat.FacebookError:
            return  # Failed loading from cookies
