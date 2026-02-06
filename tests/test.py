"""
Test script for nginx endpoints.
- Port 8080: expects HTTP 200 with HTML content + rate limiting
- Port 8081: expects HTTP 418 error response
"""

import sys
import time
import urllib.request
import urllib.error

NGINX_HOST = "nginx"
MAX_RETRIES = 30


def wait_for_nginx():
    """Wait for nginx to be ready."""
    for i in range(MAX_RETRIES):
        try:
            urllib.request.urlopen(f"http://{NGINX_HOST}:8080/", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def test_html_endpoint():
    """Test port 8080 returns 200 with HTML content."""
    try:
        resp = urllib.request.urlopen(f"http://{NGINX_HOST}:8080/", timeout=5)
        body = resp.read().decode()
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        assert "Hello from Nginx" in body, "Missing expected content"
        print("Port 8080: PASS (200 OK)")
        return True
    except Exception as e:
        print(f"Port 8080: FAIL ({e})")
        return False


def test_error_endpoint():
    """Test port 8081 returns 418 error."""
    try:
        urllib.request.urlopen(f"http://{NGINX_HOST}:8081/", timeout=5)
        print("Port 8081: FAIL (expected error, got success)")
        return False
    except urllib.error.HTTPError as e:
        if e.code == 418:
            print("Port 8081: PASS (418 I'm a teapot)")
            return True
        print(f"Port 8081: FAIL (expected 418, got {e.code})")
        return False
    except Exception as e:
        print(f"Port 8081: FAIL ({e})")
        return False


def test_rate_limiting():
    """Test rate limiting returns 429 when exceeded."""
    url = f"http://{NGINX_HOST}:8080/"
    got_429 = False
    
    # Send 20 rapid requests - should trigger rate limit (5 req/s + burst of 10)
    for i in range(20):
        try:
            urllib.request.urlopen(url, timeout=1)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                got_429 = True
                break
        except Exception:
            pass
    
    if got_429:
        print("Rate limit: PASS (429 received)")
        return True
    else:
        print("Rate limit: FAIL (no 429 received)")
        return False


if __name__ == "__main__":
    print("Testing nginx endpoints...")
    
    if not wait_for_nginx():
        print("FAIL: nginx not ready")
        sys.exit(1)
    
    results = [test_html_endpoint(), test_error_endpoint(), test_rate_limiting()]
    
    if all(results):
        print("All tests passed")
        sys.exit(0)
    else:
        print("Some tests failed")
        sys.exit(1)
