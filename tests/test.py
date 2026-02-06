"""
Test script for nginx endpoints.
- Port 8080: HTTP 200 with HTML content + rate limiting
- Port 8081: HTTP 418 error response
"""

import sys
import time
import urllib.request
import urllib.error

NGINX_HOST = "nginx"
MAX_RETRIES = 30


def fetch(url, timeout=5):
    """
    Fetch URL and return (status_code, body).
    Returns status code even for HTTP errors.
    """
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode() if e.fp else ""
    except Exception as e:
        return None, str(e)


def wait_for_nginx():
    """Wait for nginx to be ready."""
    for _ in range(MAX_RETRIES):
        status, _ = fetch(f"http://{NGINX_HOST}:8080/", timeout=2)
        if status == 200:
            return True
        time.sleep(1)
    return False


def test_html_endpoint():
    """Test port 8080 returns 200 with HTML content."""
    status, body = fetch(f"http://{NGINX_HOST}:8080/")
    assert status == 200, f"Expected 200, got {status}"
    assert "Hello from Nginx" in body, "Missing expected content"
    print("Port 8080: PASS (200 OK)")


def test_error_endpoint():
    """Test port 8081 returns 418 error."""
    status, _ = fetch(f"http://{NGINX_HOST}:8081/")
    assert status == 418, f"Expected 418, got {status}"
    print("Port 8081: PASS (418 I'm a teapot)")


def test_rate_limiting():
    """Test rate limiting returns 429 when exceeded."""
    url = f"http://{NGINX_HOST}:8080/"
    
    # Send 20 rapid requests - should trigger rate limit
    for _ in range(20):
        status, _ = fetch(url, timeout=1)
        if status == 429:
            print("Rate limit: PASS (429 received)")
            return
    
    raise AssertionError("Rate limit: no 429 received")


if __name__ == "__main__":
    print("Testing nginx endpoints...")
    
    assert wait_for_nginx(), "nginx not ready"
    
    tests = [test_html_endpoint, test_error_endpoint, test_rate_limiting]
    failed = []
    
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"{test.__name__}: FAIL ({e})")
            failed.append(test.__name__)
    
    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)
    
    print("All tests passed")
    sys.exit(0)
