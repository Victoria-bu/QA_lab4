from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.checkout_page import CheckoutPage


def test_full_purchase_flow(page):
    login = LoginPage(page)
    inventory = InventoryPage(page)
    checkout = CheckoutPage(page)

    login.navigate()
    login.login("standard_user", "secret_sauce")
    
    inventory.add_backpack_to_cart()
    inventory.go_to_cart()
    page.locator("#checkout").click() 

    checkout.fill_info("Viktoriia", "QA", "01001")
    checkout.finish_checkout()

    assert checkout.get_success_message() == "Thank you for your order!"

def test_sort_prices_low_to_high(page):
    login = LoginPage(page)
    inventory = InventoryPage(page)

    login.navigate()
    login.login("standard_user", "secret_sauce")
    
    inventory.sort_by_price_low_to_high()

    assert inventory.get_first_item_price() == "$7.99"