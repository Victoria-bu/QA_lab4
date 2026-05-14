class InventoryPage:
    def __init__(self, page):
        self.page = page
        self._add_backpack_btn = page.locator("#add-to-cart-sauce-labs-backpack")
        self._cart_link = page.locator(".shopping_cart_link")
        self._cart_badge = page.locator(".shopping_cart_badge")
        self._sort_dropdown = page.locator(".product_sort_container")
        self._first_item_price = page.locator(".inventory_item_price").first

        
    def add_backpack_to_cart(self):
        self._add_backpack_btn.click()

    def go_to_cart(self):
        self._cart_link.click()

    def get_cart_items_count(self):
        return self._cart_badge.inner_text()

    def sort_by_price_low_to_high(self):
        self._sort_dropdown.select_option("lohi")

    def get_first_item_price(self):
        return self._first_item_price.inner_text()