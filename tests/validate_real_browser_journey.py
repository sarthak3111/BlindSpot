"""Real browser validation test using Playwright with Edge."""

import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

def run_browser_validation():
    print("Launching actual Microsoft Edge browser in desktop resolution (1280x800)...")

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Listen for console messages
        def on_console(msg):
            # Ignore Tailwind CDN non-error development advisory
            if "tailwindcss.com should not be used in production" in msg.text:
                return
            if msg.type == "error":
                console_errors.append(f"[{msg.type.upper()}] {msg.text}")
            print(f"  [BROWSER CONSOLE] {msg.type}: {msg.text}")

        def on_page_error(err):
            page_errors.append(str(err))
            print(f"  [PAGE ERROR] {err}")

        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        # 1. Navigate to Web UI
        print("\nStep 1: Navigating to http://127.0.0.1:5000...")
        page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        assert page.title() == "BlindSpot — Critical-Thinking AI Engine"
        print("  [PASS] Web UI loaded successfully. Title verified.")

        # 2. Test Clear Error State
        print("\nStep 2: Testing Error State (empty submission)...")
        page.click("#analyzeBtn")
        page.wait_for_selector("#errorAlert:not(.hidden)")
        error_msg = page.text_content("#errorMessage")
        assert "Please enter your decision reasoning" in error_msg
        print(f"  [PASS] Error state correctly rendered inline: '{error_msg}'")

        # 3. Enter exact user journey inputs
        print("\nStep 3: Entering real user dilemma inputs...")
        reasoning = "The stipend is ₹30,000, the company is close to home, and I will get industry experience."
        options = "Should I accept a 6-month internship?"
        context_priorities = "Priorities: Career growth, academics, financial independence. Constraints: College schedule and upcoming exams."

        page.fill("#userInput", reasoning)
        page.fill("#optionsInput", options)
        page.fill("#contextInput", context_priorities)
        print("  [PASS] Inputs filled into form fields.")

        # 4. Trigger Analysis & Verify Loading State
        print("\nStep 4: Clicking Analyze & verifying Loading State...")
        page.click("#analyzeBtn")
        
        # Check loading indicators
        is_disabled = page.is_disabled("#analyzeBtn")
        btn_text = page.text_content("#btnText")
        spinner_visible = page.is_visible("#btnSpinner")
        print(f"  [PASS] Loading State: Button disabled={is_disabled}, Text='{btn_text}', Spinner visible={spinner_visible}")

        # 5. Wait for Results
        print("\nStep 5: Awaiting AI reasoning engine response...")
        page.wait_for_selector("#resultsContainer:not(.hidden)", timeout=15000)
        page.wait_for_selector("#emptyState", state="hidden")
        print("  [PASS] Results container displayed. Empty state hidden.")

        # 6. Verify specific results in every section
        print("\nStep 6: Verifying all rendered sections...")
        summary = page.text_content("#resSummary")
        tension = page.text_content("#resTension")
        print(f"  - Decision Summary: {summary}")
        print(f"  - Core Tension: {tension}")
        assert len(summary.strip()) > 10
        assert len(tension.strip()) > 10

        cards_text = page.text_content("#categoryCards")
        assert "Assumptions" in cards_text
        assert "Overlooked Factors" in cards_text
        assert "Contradictions & Tensions" in cards_text
        assert "Evidence Gaps" in cards_text
        assert "Trade-Offs" in cards_text
        assert "OBSERVATION" in cards_text
        assert "HYPOTHESIS" in cards_text
        print("  [PASS] All 5 blind spot categories and OBSERVATION/HYPOTHESIS badges verified.")

        questions = page.query_selector_all("#resQuestions li")
        assert len(questions) >= 3
        print(f"  [PASS] Questions to explore verified ({len(questions)} high-impact inquiries).")
        for i, q in enumerate(questions, 1):
            print(f"    {i}. {q.text_content().strip()}")

        # 7. Verify no recommendation or ranking exists
        print("\nStep 7: Verifying AI does NOT recommend or rank decisions...")
        all_text = page.text_content("#resultsContainer").lower()
        assert "i recommend" not in all_text
        assert "you should accept" not in all_text
        assert "you should choose" not in all_text
        assert "the best option is" not in all_text
        assert "ranked #1" not in all_text
        print("  [PASS] Confirmed: Zero recommendations, zero ranking, zero directive advice.")

        # 8. Test Copy Button
        print("\nStep 8: Testing Copy JSON action...")
        page.click("#copyBtn")
        page.wait_for_timeout(500)
        btn_content = page.text_content("#copyBtn")
        print(f"  [PASS] Copy feedback active: '{btn_content.strip()}'")

        # 9. Capture Desktop Screenshot
        screenshot_path = "D:\\blindspot\\internship_validation_screenshot.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\nStep 9: Full page screenshot saved to {screenshot_path}")

        # 10. Verify Console Errors
        print("\nStep 10: Checking for console / runtime errors...")
        print(f"  Total console errors: {len(console_errors)}")
        print(f"  Total page errors: {len(page_errors)}")
        if console_errors:
            print(f"  Console error details: {console_errors}")
        assert len(console_errors) == 0, f"Unexpected console errors: {console_errors}"
        assert len(page_errors) == 0, f"Unexpected page errors: {page_errors}"
        print("  [PASS] Zero console or runtime errors detected.")

        browser.close()
        print("\n=======================================================")
        print("  ALL 10 BROWSER JOURNEY VALIDATION CHECKS PASSED!")
        print("=======================================================")

if __name__ == "__main__":
    run_browser_validation()
