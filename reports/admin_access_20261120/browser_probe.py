"""Disposable browser acceptance. Credentials and tokens stay in process memory."""
import base64
import hmac
import os
import secrets
import subprocess
import time
import urllib.request

import pexpect
from playwright.sync_api import expect, sync_playwright

container = os.environ["CV_PROBE_CONTAINER"]
origin = "http://127.0.0.1:18087"
email = "bootstrap-owner@example.org"
password = "Cv!42-" + secrets.token_urlsafe(24)
def bootstrap(address, expected_exit):
    child = pexpect.spawn("docker", ["exec", "-it", container, "python", "-m", "app.cli", "create-admin"], encoding="utf-8", timeout=20)
    for prompt, value in (
        ("Administrator email: ", address),
        ("Administrator password: ", password),
        ("Confirm password: ", password),
    ):
        child.expect_exact(prompt)
        child.sendline(value)
    child.expect_exact("Administrator account created." if expected_exit == 0 else "Initial administrator already exists")
    child.expect(pexpect.EOF)
    child.close()
    assert child.exitstatus == expected_exit


def ready():
    for _ in range(40):
        try:
            with urllib.request.urlopen(origin + "/api/health/ready", timeout=2):
                return
        except OSError:
            time.sleep(1)
    raise RuntimeError("Service readiness timed out")

def code(secret):
    digest = hmac.digest(base64.b32decode(secret), (int(time.time()) // 30).to_bytes(8, "big"), "sha1")
    offset = digest[-1] & 15
    return f"{(int.from_bytes(digest[offset:offset+4], 'big') & 0x7fffffff) % 1_000_000:06d}"

ready()
bootstrap(email, 0)
bootstrap("other@example.org", 2)
with sync_playwright() as runner:
    browser = runner.chromium.launch()
    page = browser.new_page()
    page.goto(origin)
    page.locator("#email").fill(email)
    page.locator("#password").fill(password)
    page.get_by_role("button", name="Sign in", exact=True).click()
    setup = page.locator(".wm-auth-help code")
    expect(setup).to_be_visible()
    page.get_by_label("Authenticator code").fill(code(setup.inner_text()))
    page.get_by_role("button", name="Sign in", exact=True).click()
    entry = page.get_by_role("heading", name="User Management", exact=True)
    expect(entry).to_be_visible()
    entry.locator("..").get_by_role("button").click()
    page.get_by_label("Invite by email").fill("invited@example.org")
    page.get_by_role("button", name="Create invitation").click()
    link = page.get_by_label("Invitation link", exact=False)
    expect(link).to_be_visible()
    invite_url = link.input_value()
    invited = browser.new_page()
    invited.goto(invite_url)
    invited.locator("#username").fill("invited_user")
    invited.locator("#email").fill("invited@example.org")
    invited.locator("#password").fill(password)
    invited.get_by_role("button", name="Create account", exact=True).click()
    expect(invited.get_by_role("button", name="User Management", exact=True)).to_have_count(0)
    expect(invited.locator("#email")).to_have_count(0)
    assert page.evaluate("localStorage.getItem('artery-analysis-token')") is None
    assert invited.evaluate("localStorage.getItem('artery-analysis-token')") is None
    subprocess.run(["docker", "restart", container], check=True, capture_output=True)
    ready()
    page.reload()
    expect(page.get_by_text("Administrator", exact=True).first).to_be_visible()
    print("PASS: Docker first admin, browser MFA, invitation redemption, session storage and restart")
