class CheckoutPage:
    def __init__(self, page):
        self.page = page
        self._first_name = page.locator("#first-name")
        self._last_name = page.locator("#last-name")
        self._zip_code = page.locator("#postal-code")
        self._continue_btn = page.locator("#continue")
        self._finish_btn = page.locator("#finish")
        self._success_message = page.locator(".complete-header")

    def fill_info(self, first, last, zip):
        self._first_name.fill(first)
        self._last_name.fill(last)
        self._zip_code.fill(zip)
        self._continue_btn.click()

    def finish_checkout(self):
        self._finish_btn.click()

    def get_success_message(self):
        return self._success_message.inner_text()