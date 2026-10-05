from playwright.sync_api import Playwright

def create_authenticated_session(playwright:Playwright):
    api_request_context = playwright.request.new_context(base_url="https://api.eventhub.rahulshettyacademy.com/api")
    response = api_request_context.post("api/auth/login",data={"email":"rahul@gmail.com","password":"Welcome@5"})
    result = response.json()
    print("Status:", response.status)
    print("URL:", response.url)
    api_request_context.dispose()
    return result["token"]

def get_events(playwright:Playwright,token):
    api_request_context = playwright.request.new_context(base_url="https://api.eventhub.rahulshettyacademy.com/")
    event_details = api_request_context.get("api/events",headers={"Authorization":f"Bearer {token}"})
    event = event_details.json()
    api_request_context.dispose()
    return event
def create_booking(playwright:Playwright,token,event):
    payload = {
        "customerName": "test",
        "customerEmail": "rahul@gmail.com",
        "customerPhone": "78945612378",
        "quantity": 2,
        "eventId":event["id"]
    }
    api_request_context = playwright.request.new_context(base_url="https://api.eventhub.rahulshettyacademy.com/")
    response = api_request_context.post("api/bookings",data=payload,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"})
    result = response.json()
    api_request_context.dispose()
    return result

def get_booking_response(playwright:Playwright,result,token):
    api_request_context = playwright.request.new_context(base_url="https://api.eventhub.rahulshettyacademy.com/")
    response = api_request_context.get(f"api/bookings/{result["data"]['id']}",headers={"Authorization":f"Bearer {token}"})
    api_request_context.dispose()
    return response.json()["data"]

def delete_booking(playwright:Playwright,result,token):
    api_request_context = playwright.request.new_context(base_url="https://api.eventhub.rahulshettyacademy.com/")
    response = api_request_context.delete(f"api/bookings/{result["data"]['id']}",headers={"Authorization":f"Bearer {token}"})
    api_request_context.dispose()
    return response.status