import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

APP_URL = "https://subjective-perception-for-historic-centres.streamlit.app/"

WAKE_KEYWORDS = [
    "wake",
    "activate",
    "get this app back up",
    "yes",
    "rerun",
    "start",
]


def make_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,1000")
    return webdriver.Chrome(options=options)


def click_wake_button_if_present(driver):
    buttons = driver.find_elements(By.TAG_NAME, "button")

    for button in buttons:
        text = (button.text or "").strip().lower()
        aria = (button.get_attribute("aria-label") or "").strip().lower()
        combined = f"{text} {aria}"

        if any(keyword in combined for keyword in WAKE_KEYWORDS):
            print(f"Found possible wake button: {combined}")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", button)
            return True

    return False


def main():
    driver = make_driver()

    try:
        print(f"Opening: {APP_URL}")
        driver.get(APP_URL)

        time.sleep(10)

        clicked = click_wake_button_if_present(driver)

        if clicked:
            print("Wake/activate button clicked. Waiting for app to load...")
            time.sleep(60)
        else:
            print("No wake button found. The app may already be active.")

        driver.get(APP_URL)
        time.sleep(25)

        page_text = driver.find_element(By.TAG_NAME, "body").text

        print("Page text preview:")
        print(page_text[:800])

        if "Subjective Perception" in page_text or "Subjective Perceptions" in page_text:
            print("Success: survey page appears to be loaded.")
        else:
            print("Warning: survey title not detected, but page was visited.")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
