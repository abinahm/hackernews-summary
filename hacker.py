import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

URL1 = "https://thehackernews.com/"
URL2 = "https://gemini.google.com/app"
PROFILE_DIR = r"C:\edge_gemini_profile"  # separate profile, keeps your login

EDITOR = "rich-textarea div[contenteditable='true'], div.ql-editor[contenteditable='true']"
RESPONSE = "message-content"

opts = Options()
opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Edge(options=opts)
wait = WebDriverWait(driver, 30)

try:
    # 1. Scrape the front page
    driver.get(URL1)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.body-post")))
    stories = []
    for post in driver.find_elements(By.CSS_SELECTOR, "div.body-post"):
        try:
            title = post.find_element(By.CSS_SELECTOR, ".home-title").text.strip()
        except Exception:
            continue
        try:
            desc = post.find_element(By.CSS_SELECTOR, ".home-desc").text.strip()
        except Exception:
            desc = ""
        stories.append(f"- {title}: {desc}")

    if not stories:
        raise SystemExit("No stories found. The site's HTML may have changed.")

    prompt = (
        "Here are today's headlines from The Hacker News. Give me a concise "
        "morning briefing: group related stories, highlight anything critical "
        "(actively exploited vulnerabilities, major breaches), and keep it "
        "scannable.\n\n" + "\n".join(stories)
    )

    # 2. Open Gemini
    driver.get(URL2)
    try:
        box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, EDITOR))
        )
    except TimeoutException:
        input("Log in to Google in the browser window, then press Enter here... ")
        driver.get(URL2)
        box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, EDITOR)))

    # 3. Paste the prompt (insertText keeps newlines without triggering send)
    box.click()
    driver.execute_script(
        "arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);",
        box, prompt,
    )
    time.sleep(1)
    box.send_keys(Keys.ENTER)

    # 4. Wait for the answer to finish streaming (text stops changing)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, RESPONSE)))
    last, stable = "", 0
    while stable < 4:
        time.sleep(2)
        els = driver.find_elements(By.CSS_SELECTOR, RESPONSE)
        text = els[-1].text if els else ""
        if text and text == last:
            stable += 1
        else:
            stable, last = 0, text

    print("\n" + "=" * 60)
    print("HACKER NEWS MORNING BRIEF")
    print("=" * 60 + "\n")
    print(last)

finally:
    driver.quit()