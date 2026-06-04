from playwright.sync_api import sync_playwright

def generate_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to login...")
        # Start at the main login portal
        page.goto("https://myaccount.ctclink.us/")
        
        print("=========================================")
        print("⏳ YOU HAVE 2 MINUTES TO:")
        print("1. Log in and pass phone verification.")
        print("2. Navigate ALL THE WAY to the BIO 241 class search page.")
        print("3. Stay on that page until this timer finishes.")
        print("=========================================")
        
        # Pauses for exactly 120 seconds
        page.wait_for_timeout(120000) 
        
        print("Saving session state now...")
        context.storage_state(path="state.json")
        print("✅ Session saved successfully to state.json!")
        browser.close()

if __name__ == "__main__":
    generate_state()