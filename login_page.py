class LoginPage:
    def __init__(self, page):
        self.page = page
        self._username = page.locator("#user-name")
        self._password = page.locator("#password")
        self._login_btn = page.locator("#login-button")

    def navigate(self):
        self.page.goto("https://www.saucedemo.com/")

    def login(self, user, pwd):
        self._username.fill(user)
        self._password.fill(pwd)
        self._login_btn.click()