import json
import re
import time
from asyncio.windows_events import NULL

from playwright.sync_api import Playwright, expect
from pytest_playwright.pytest_playwright import browser

from temp.apiutils import Apiutils


import json
import time

from playwright.sync_api import Playwright, expect



preserved_id = 5986
patched_values={}

def intercept_request(route):
    response = route.fetch()
    data = response.json()
    patch_bookings = data ["data"][0]
    patch_bookings["bookingRef"] = "MOCK-REF-7"
    patch_bookings["event"]["title"] = "Mock AI Event"
    patch_bookings["quantity"] = 700
    patch_bookings["totalPrice"] = 2000
    patch_bookings["id"] = preserved_id
    route.fulfill(
        response=response,
        json = data
    )

# def intercept_request(route):
#
#     response = route.fetch()
#
#     print("STATUS:", response.status)
#     print("URL:", response.url)
#
#     data = response.json()
#
#     print("DATA:", data)
#
#     if not data["data"]:
#         print("***** EMPTY BOOKING RESPONSE *****")
#         route.fulfill(response=response, json=data)
#         return
#
#     patch_bookings = data["data"][0]
#
#     print("ORIGINAL BOOKING:", patch_bookings)
#
#     # your modifications here
#
#     route.fulfill(
#         response=response,
#         json=data
#     )

def intercept_response(route):
    response = route.fetch()

    data = response.json()
    patchbooking = data ["data"]
    patchbooking["bookingRef"] = "MOCK-REF-9"
    patchbooking["event"]["title"] = "Mock digital Event"
    patchbooking["quantity"] = 200
    patchbooking["event"]["price"] = 1000
    patchbooking["totalPrice"] = patchbooking["quantity"] * patchbooking["event"]["price"]
    patchbooking["id"] = preserved_id
    patchbooking["customerEmail"] = "rahul@gmail.com"

    patched_values["bookingRef"] = patchbooking["bookingRef"]
    patched_values["title"] = patchbooking["event"]["title"]
    patched_values["quantity"] = patchbooking["quantity"]
    patched_values["totalPrice"] = patchbooking["event"]["price"]
    patched_values["total_paid"] = patchbooking["totalPrice"]
    patched_values["email"] = patchbooking["customerEmail"]

    route.fulfill(
        response=response,
        json=data
    )


def test_login(playwright: Playwright):
    apiutils = Apiutils()

    # API login
    token = apiutils.get_token(playwright)

    print("API token:", token)

    # Browser
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Inject token BEFORE page loads
    page.add_init_script(
        f'localStorage.setItem("eventhub_token", {json.dumps(token)})'
    )

    # Open application
    page.goto("https://eventhub.rahulshettyacademy.com/")

    time.sleep(5)

    print("Current URL:", page.url)
    print("Title:", page.title())

    print(page.locator("body").inner_text())

    # Now verify an authenticated UI element
    expect(page.get_by_test_id("nav-bookings")).to_be_visible()
    page.route("https://api.eventhub.rahulshettyacademy.com/api/bookings?**",intercept_request)

    # open My Bookings and confirm the My Bookings heading is visible.
    my_bookings = page.get_by_test_id("nav-bookings")
    my_bookings.click()
    my_bookings_heading = page.locator("h1").filter(has_text="My Bookings")
    expect(my_bookings_heading).to_be_visible()
    patchcard = page.get_by_text("MOCK-REF-7").locator("xpath = ancestor::div[@data-testid='booking-card']")
    expect(patchcard.get_by_text("Mock AI Event")).to_be_visible()
    expect(patchcard.get_by_text("700")).to_be_visible()
    expect(patchcard.get_by_text("$2,000")).to_be_visible()

    expect(page.get_by_text("Dilli Diwali Mela").first).to_be_visible()
    event_card_cnt = page.get_by_test_id("booking-card").count()
    print(event_card_cnt)
    all_eventcard_texts =  page.get_by_test_id("booking-card").locator('h3').all_text_contents()

    other_live_titles = [
        title for title in all_eventcard_texts
        if title != "Mock AI Event"
    ]
    assert other_live_titles, "No other live booking title found"
    all_eventcard_texts = page.get_by_test_id("booking-card").locator("h3").all_text_contents()

    for eventtext in all_eventcard_texts:
        if eventtext != "Mock AI Event":
            assert eventtext, "Event card other than Mock AI Event found"
    page.route(f"https://api.eventhub.rahulshettyacademy.com/api/bookings/{preserved_id}", intercept_response)
    viewdetailsbtn_patchcard = patchcard.get_by_role("link",name = "View Details").first
    viewdetailsbtn_patchcard.click()

    print(page.url)
    expect(page).to_have_url(f"https://eventhub.rahulshettyacademy.com/bookings/{preserved_id}")
    expect(page.get_by_role("link",name = "← Back to My Bookings")).to_be_visible()
    expect(page.get_by_text("MOCK-REF-9").nth(1)).to_be_visible()
    #Confirm the detail page breadcrumb/reference, title, payment summary tickets, and total paid
    # match the patched values, and the customer email still matches the original live value.

    expect(page.get_by_role("link", name="My Bookings").nth(1)).to_be_visible()
    expect(page.get_by_text("MOCK-REF-9", exact=True).nth(0)).to_be_visible()
    ticket_row = page.get_by_text("Tickets").locator('..')
    ticket_value = ticket_row.locator("span").nth(1).inner_text()
    assert int(ticket_value) == patched_values["quantity"]
    price_per_ticket_row = page.get_by_text("Price per ticket").locator('..')
    totalprice = price_per_ticket_row.locator('span').nth(1).inner_text()
    patchedprice = int(totalprice.replace("$","").replace(",",""))
    assert patchedprice == patched_values["totalPrice"]
    total_paid_row = page.get_by_text("Total Paid").locator('..')
    total = int(total_paid_row.locator("span").nth(1).inner_text().replace("$","").replace(",",""))
    assert total == patched_values["total_paid"]
    customer_email_row = page.get_by_text("Email").locator('..')
    customer_email = customer_email_row.locator("span").nth(1).inner_text()
    assert customer_email == patched_values["email"]
    back_to_bookings = page.get_by_role("link", name="← Back to My Bookings")
    back_to_bookings.click()
    expect(my_bookings_heading).to_be_visible()
    expect(patchcard.get_by_text("MOCK-REF-7")).to_be_visible()