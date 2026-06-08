import os
import time
import datetime
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load passwords from the .env file locally
load_dotenv()

# --- CONFIGURATION ---
CLASS_URL = "https://csprd.ctclink.us/psc/csprd_6/EMPLOYEE/SA/c/SSR_STUDENT_FL.SSR_MD_CRSEINFO_FL.GBL?Action=U&MD=Y&GMenu=SSR_STUDENT_FL&GComp=SSR_START_PAGE_FL&GPage=SSR_START_PAGE_FL&scname=CS_SSR_MANAGE_CLASSES_NAV"

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def send_notification(subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)
    print(f"Email sent: {subject}")

def check_status():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="state.json")
        page = context.new_page()
        
        try:
            print("Navigating directly to the class search page...")
            page.goto(CLASS_URL)
            page.wait_for_timeout(5000) 
            
            if "login" in page.url.lower() or "authentication" in page.url.lower():
                print("❌ Session expired! Redirected to login page.")
                send_notification(
                    "⚠️ Action Required: Update state.json Session",
                    "Your class scraper hit a login wall. Run your local save_state.py script to generate a fresh state.json."
                )
                return

            # --- NEW SEARCH PHASE ---
            print("Searching for BIOL& 241...")
            search_bar_selector = "#PTS_KEYWORDS3"
            
            try:
                page.wait_for_selector(search_bar_selector, timeout=10000)
                page.fill(search_bar_selector, "BIOL& 241")
                page.keyboard.press("Enter")
                print("Search submitted. Waiting for results to load...")
                
                result_link_selector = "[id='PTS_LIST_TITLE$0']"
                page.wait_for_selector(result_link_selector, timeout=15000)
                page.click(result_link_selector)
                print("Clicked the BIOL& 241 link. Loading class tables...")
                
                page.wait_for_timeout(5000)
                
            except Exception:
                print("❌ Could not complete the search phase. Double check the search bar or link ID.")
                return
            # ------------------------

            print("Checking seat availability...")
            
            try:
                page.wait_for_selector("tr.ps_grid-row", timeout=15000)
            except Exception:
                print("❌ Table didn't load. Double checking if we got locked out...")
                send_notification(
                    "⚠️ Action Required: Update state.json Session",
                    "The class data failed to load. Your session state may have expired. Please check your state.json file."
                )
                return
            
            rows = page.locator("tr.ps_grid-row")
            row_count = rows.count()
            print(f"Found {row_count} class options.")
            
            seat_opened = False
            
            for i in range(row_count):
                row = rows.nth(i)
                class_details = row.locator("td.CMPNT_CLASS_NBR").inner_text().strip()
                seat_spans = row.locator("td.SEATS span.ps_box-value")
                span_count = seat_spans.count()
                
                for j in range(span_count):
                    status_text = seat_spans.nth(j).inner_text().strip()
                    print(f"Option {i+1} status: {status_text}")
                    
                    if status_text != "Closed" and status_text != "":
                        seat_opened = True
                        print(f"🚨 AVAILABILITY FOUND IN OPTION {i+1}!")
                        email_body = (
                            f"A section changed status to: {status_text}\n\n"
                            f"Class Details:\n{class_details}\n\n"
                            f"Check the enrollment portal immediately!"
                        )
                        send_notification("🚨 Seat Opened Up in BIOL& 241!", email_body)
                        break 
                
                if seat_opened:
                    break
            
            if not seat_opened:
                print("All sections are still closed.")
                
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    print("Starting the smart local seat checker...")
    while True:
        # Get the current hour (0-23 format) based on your laptop's clock
        current_hour = datetime.datetime.now().hour
        
        # Check if the time is between 8 AM (8) and 9:59 PM (21)
        if 8 <= current_hour < 22:
            print(f"\n[{datetime.datetime.now().strftime('%I:%M %p')}] Within active hours. Checking portal...")
            check_status()
        else:
            print(f"\n[{datetime.datetime.now().strftime('%I:%M %p')}] Outside of 8 AM - 10 PM window. Skipping check.")
            
        print("Sleeping for 14 minutes...")
        time.sleep(840) # 840 seconds = 14 minutes
