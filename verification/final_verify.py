from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 900})
        page.goto("http://127.0.0.1:8080/index.html")
        page.wait_for_load_state("networkidle")

        # Setup Admin and Knockout
        page.evaluate("""() => {
            isAdmin = true;
            document.body.classList.add('admin-active');
            activeTab = 4;
            renderAll();
        }""")

        # Open Modal for M73
        page.evaluate("openMatchEvents('M73')")
        time.sleep(1)

        # Select Penalty to show UI change
        page.evaluate("""() => {
            const sel = document.getElementById('selTypeHome');
            sel.value = 'penalty';
            toggleMinuteInput('h');
            document.getElementById('videoHome').value = 'shootout.mp4';
        }""")

        page.screenshot(path="verification/penalty_admin_ui.png")
        browser.close()

run()
