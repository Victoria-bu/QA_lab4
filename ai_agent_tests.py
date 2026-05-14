"""
    export BROWSER_USE_API_KEY="....my key......"
    python ai_agent_tests.py 
"""

import asyncio
import os
import sys
from browser_use_sdk import AsyncBrowserUse
from google import genai

BROWSER_USE_API_KEY = os.environ.get("BROWSER_USE_API_KEY", "YOUR_BROWSER_USE_API_KEY")
GOOGLE_API_KEY  = os.environ.get("GOOGLE_API_KEY", "AIzaSyBIIR2eJNyMU1rhrvgSta_huumRi4OuQYU")

bu_client = AsyncBrowserUse(api_key=BROWSER_USE_API_KEY)
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

CHECKOUT_E2E_PROMPT = """
You are a QA automation agent. Execute the following test case exactly:

1. Navigate to https://www.saucedemo.com/
2. Enter 'standard_user' into the Username field.
3. Enter 'secret_sauce' into the Password field.
4. Click the 'Login' button and wait for the product list page to load.
5. Find 'Sauce Labs Backpack' and click its 'Add to cart' button.
6. Click the shopping cart icon (top right corner).
7. Confirm you are on '/cart.html'.
8. Click the 'Checkout' button.
9. Enter 'Viktoriia' into First Name, 'Buksha' into Last Name, '88888' into Postal Code.
10. Click 'Continue'.
11. Confirm the URL contains '/checkout-step-two.html'.
12. Click the 'Finish' button.

Expected Results:
- URL contains '/checkout-complete.html'.
- Page displays 'Thank you for your order!'.

End your response with RESULT: PASS or RESULT: FAIL, then a short explanation.
"""

SORT_PROMPT = """
You are a QA automation agent. Execute the following test case exactly:

1. Navigate to https://www.saucedemo.com/
2. Enter 'standard_user' into the Username field.
3. Enter 'secret_sauce' into the Password field.
4. Click the 'Login' button and wait for the product list page to load.
5. Find the sorting dropdown (default: 'Name (A to Z)').
6. Select 'Price (low to high)' from the dropdown.
7. Read the price of the very first product in the updated list.

Expected Results:
- The first product price is exactly '$7.99'.

End your response with RESULT: PASS or RESULT: FAIL, then a short explanation.
"""

REMOVE_PRODUCT_PROMPT = """
You are a QA automation agent. Execute the following test case exactly:

1. Navigate to https://www.saucedemo.com/
2. Enter 'standard_user' into the Username field.
3. Enter 'secret_sauce' into the Password field.
4. Click the 'Login' button and wait for the product list page to load.
5. Find 'Sauce Labs Bolt T-Shirt' and click its 'Add to cart' button.
6. Verify the cart badge shows '1'.
7. Click the cart icon to go to '/cart.html'.
8. Locate 'Sauce Labs Bolt T-Shirt' in the cart.
9. Click the 'Remove' button for that product.
10. Check: is the item gone? Is the badge empty? Are you still on '/cart.html'?

Expected Results:
- 'Sauce Labs Bolt T-Shirt' is no longer in the cart.
- Cart badge disappears or shows '0'.
- You remain on '/cart.html'.

End your response with RESULT: PASS or RESULT: FAIL, then a short explanation.
"""


def determine_status(result_text: str) -> str:
    """
    Спочатку парсимо RESULT: PASS/FAIL з тексту агента.
    Якщо агент не написав явно — пробуємо Gemini як fallback.
    """
    upper = result_text.upper()

    if "RESULT: PASS" in upper:
        return "PASS"
    if "RESULT: FAIL" in upper:
        return "FAIL"

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""You are a QA evaluator. Based on this browser agent output, did the test pass or fail? Reply with only: RESULT: PASS or RESULT: FAIL

Agent output:
{result_text}
""",
        )
        verdict = response.text.strip().upper()
        if "RESULT: PASS" in verdict:
            return "PASS"
        if "RESULT: FAIL" in verdict:
            return "FAIL"
    except Exception as e:
        print(f"  (Gemini fallback недоступний: {e})")

    positive = ["successfully", "thank you", "completed", "verified", "confirmed"]
    negative = ["failed", "error", "could not", "unable", "not found"]
    pos = sum(1 for w in positive if w in result_text.lower())
    neg = sum(1 for w in negative if w in result_text.lower())
    return "PASS" if pos > neg else "FAIL"


async def run_test(test_name: str, prompt: str) -> dict:
    print(f"\n  ЗАПУСК: {test_name}\n")

    try:
        task = await bu_client.tasks.create_task(task=prompt)
        task_id = task.id
        print(f"  Task ID: {task_id}")

        max_wait = 300
        interval = 5
        elapsed  = 0
        result_text = ""

        while elapsed < max_wait:
            await asyncio.sleep(interval)
            elapsed += interval

            status_obj = await bu_client.tasks.get_task_status(task_id)
            state = getattr(status_obj, "status", "unknown")
            print(f"  [{elapsed:3d}s] статус: {state}")

            if state in ("finished", "completed", "done", "success"):
                full = await bu_client.tasks.get_task(task_id)
                result_text = (
                    getattr(full, "output", None)
                    or getattr(full, "result", None)
                    or getattr(status_obj, "output", None)
                    or str(full)
                )
                break
            elif state in ("failed", "error", "cancelled"):
                result_text = f"Task ended with state: {state}"
                break

        if not result_text:
            result_text = "Timeout: task did not finish within 5 minutes."

        print(f"\n  Результат агента:\n{result_text}\n")

        status = determine_status(result_text)

        return {"test": test_name, "status": status, "agent_output": result_text}

    except Exception as exc:
        print(f"\n   ПОМИЛКА: {exc}")
        return {"test": test_name, "status": "ERROR", "details": str(exc)}

async def run_all_tests():
    tests = [
        ("TC-01: Checkout E2E",   CHECKOUT_E2E_PROMPT),
        ("TC-02: Sort by Price",  SORT_PROMPT),
        ("TC-03: Remove Product", REMOVE_PRODUCT_PROMPT),
    ]
    results = []
    for name, prompt in tests:
        results.append(await run_test(name, prompt))

    print("\n  ЗВІТ\n")
    for r in results:
        print(f"{r['test']:<35} {r['status']}")
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    print(f"\n  Всього: {len(results)}  |  ✅ {passed}  |  ❌ {failed}  |  ⚠️  {errors}\n")

async def run_single(key: str):
    mapping = {
        "checkout": ("TC-01: Checkout E2E",   CHECKOUT_E2E_PROMPT),
        "sort":     ("TC-02: Sort by Price",  SORT_PROMPT),
        "remove":   ("TC-03: Remove Product", REMOVE_PRODUCT_PROMPT),
    }
    if key not in mapping:
        print(f"Невідомий тест '{key}'. Доступні: {list(mapping)}")
        return
    await run_test(*mapping[key])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(run_single(sys.argv[1].lower()))
    else:
        asyncio.run(run_all_tests())