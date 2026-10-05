from playwright.sync_api import Playwright


class Apiutils:
    def get_token(self,playwright: Playwright):
        api_request_context = playwright.request.new_context(base_url = "https://api.eventhub.rahulshettyacademy.com/")
        response = api_request_context.post("api/auth/login",data={"email":"rahul@gmail.com","password":"Welcome@5"})
        result = response.json()
        print("Status:", response.status)
        print("URL:", response.url)
        return result["token"]