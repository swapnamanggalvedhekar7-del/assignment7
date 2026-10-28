from datetime import datetime
import json
from difflib import context_diff

from playwright.sync_api import Playwright, expect

import apiutils

def test_assignment7(playwright:Playwright):
    selected_event = {}
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    # Create an authenticated API session for EventHub and keep the login token for later browser access.
    token = apiutils.create_authenticated_session(playwright)
    # Inject token BEFORE page loads
    page.add_init_script(
        f'localStorage.setItem("eventhub_token", {json.dumps(token)})'
    )
    page.goto("https://eventhub.rahulshettyacademy.com/")
    expect(page.get_by_test_id("nav-bookings")).to_be_visible()
    My_bookings = page.get_by_test_id("nav-bookings")
    My_bookings.click()
    # page.locator("button:has-text('Clear all bookings')").click()
    # page.wait_for_load_state("networkidle")
    page.locator("button:has-text('Clear all bookings')").click()
    events = apiutils.get_events(playwright, token)


    for event in events["data"]:
        if event["availableSeats"]>=2:
            #capture id, title, category, city, and price
            selected_event = {
                "id": event["id"],
                "title": event["title"],
                "category": event["category"],
                "city": event["city"],
                "price": event["price"],
                "eventDate": event["eventDate"],
                "venue": event["venue"]
            }
        # raise AssertionError(
        #         f"No bookable event found with at least {event["availableSeats"]} seats"
        #     )
            break
            assert selected_event, (
                "No bookable event found with at least 2 available seats")
    booking= apiutils.create_booking(playwright, token,selected_event)

    #Confirm the create response returns a booking id and a human-readable reference code, then store id, reference, selected event fields, and expected total for later assertions.
    data = booking["data"]
    #print(type(data))

    assert 'id' in list(data.keys()),"booking is not found in the response"
    assert 'bookingRef' in list(data.keys()), "booking reference not found in the response"
    #then store id, reference, selected event fields, and expected total
    booking_id = data["id"]
    print(booking_id)
    booking_ref = data["bookingRef"]
    booking_events = data["event"]
    booking_total = data["totalPrice"]
    #Look the booking up again by reference through the API and confirm id, reference, ticket quantity, and total match the create response.
    booking_details = apiutils.get_booking_response(playwright, booking, token)
    assert booking_details["id"]==booking_id,"Booking ID does not match"
    assert booking_details["bookingRef"] == booking_ref, "booking_ref does not match"
    assert booking_details["quantity"] == data["quantity"], "Booking quantity does not match"
    assert booking_details["totalPrice"] == booking_total, "Booking total does not match"
    page.reload()
    page.wait_for_load_state("networkidle")
    booking_card = (
        page.get_by_test_id("booking-card")
        .filter(has_text=booking_ref)
    )

    expect(booking_card).to_be_visible()
    expect(
        booking_card.get_by_text(booking_ref, exact=True)
    ).to_be_visible()
    #print(type(booking_ref))
    booking_ref_mybookings =page.get_by_test_id("booking-card").get_by_text(data["bookingRef"]).text_content()
    print(booking_ref_mybookings)
    #Confirm the card title matches the runtime-selected event title and shows two tickets with the expected total
    booking_card = (
        page.get_by_test_id("booking-card")
        .filter(has_text=booking_ref)
    )
    expect(
        booking_card.get_by_text(selected_event["title"], exact=True)
    ).to_be_visible()
    print(booking_ref_mybookings)
    #Open View Details from that card and confirm the detail path, breadcrumb/reference,
    # event details, payment summary, and customer email all match the stored API booking data.
    #page.locator('button:has-text("View Details")').click()
    booking_card.get_by_role(
        "button",
        name="View Details"
    ).click()
    expect(page).to_have_url(f"https://eventhub.rahulshettyacademy.com/bookings/{booking_id}")
    expect(page.get_by_role("link", name="My Bookings").nth(1)).to_be_visible()
    #expect(page.get_by_text(f"{booking_ref[0]}").nth(0)).to_be_visible()
    expect(
        page.get_by_text(booking_ref, exact=True).first
    ).to_be_visible()
    Event_row = page.get_by_text("Event",exact=True).locator('..')
    Event_value = Event_row.locator("span").nth(1).inner_text()
    Category_row = page.get_by_text("Category",exact=True).locator('..')
    Category_value = Category_row.locator("span").nth(1).inner_text()
    Date_row = page.get_by_text("Date").locator('..')
    Date_value = Date_row.locator("span").nth(1).inner_text()
    Venue_row = page.get_by_text("Venue").locator('..')
    Venue_value = Venue_row.locator("span").nth(1).inner_text()
    City_row = page.get_by_text("City").locator('..')
    City_value = City_row.locator("span").nth(1).inner_text()
    #identifying email id
    Email_row = page.get_by_text("Email").locator('..')
    Email_value = Email_row.locator("span").nth(1).inner_text()
    assert Event_value == selected_event["title"],"Event title does not match"
    assert Category_value == selected_event["category"],"Event Category does not match"
    api_date = selected_event["eventDate"]
    print("API date       :", repr(api_date))

    formatted_date = datetime.fromisoformat(
        api_date.replace("Z", "+00:00")
    ).strftime("%A, %d %B %Y")

    print("Formatted date :", repr(formatted_date))
    print("UI Date        :", repr(Date_value))

    assert Date_value == formatted_date, "Event Date does not match"
    # assert Date_value == selected_event["eventDate"],"Event Date does not match"
    assert Venue_value== selected_event["venue"],"Event Venue does not match"
    assert City_value == selected_event["city"], "Event City does not match"
    #email id asserted
    assert Email_value == booking_details["customerEmail"]
    ticket_row = page.get_by_text("Tickets").locator('..')
    ticket_value = ticket_row.locator("span").nth(1).inner_text()
    assert int(ticket_value) == data["quantity"]
    price_per_ticket_row = page.get_by_text("Price per ticket").locator('..')
    totalprice = price_per_ticket_row.locator('span').nth(1).inner_text()
    patchedprice = int(totalprice.replace("$", "").replace(",", ""))
    assert patchedprice == int(selected_event["price"]), "Price per ticket does not match"
    total_paid_row = page.get_by_text("Total Paid").locator('..')
    total = int(total_paid_row.locator("span").nth(1).inner_text().replace("$", "").replace(",", ""))
    assert total == int(booking_total), "total does not match"
    #Cancel/delete the booking through the authenticated API using the stored booking id
    # and confirm the delete succeeds.
    deletebooking= apiutils.delete_booking(playwright,result=booking,token=token)
    print(deletebooking)
    page.get_by_role("link",name = "← Back to My Bookings").click()
    expect(page).to_have_url("https://eventhub.rahulshettyacademy.com/bookings")
    #confirm the booking no longer appears.
    page.reload()
    expect(
        page.get_by_text(booking_ref, exact=True).first
    ).not_to_be_visible()
    context.close()
    browser.close()