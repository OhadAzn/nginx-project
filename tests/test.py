"""
Test script for nginx endpoints.
- Port 8080: HTTP redirect to HTTPS
- Port 443: HTTPS with HTML content + rate limiting
- Port 8081: HTTP 418 error response
"""

import sys
import time
import ssl
import urllib.request
import urllib.error

NGINX_HOST = "nginx"
MAX_RETRIES = 30

# SSL context for self-signed cert
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def fetch(url, timeout=5, follow_redirect=True):
    """
    Fetch URL and return (status_code, body).
    Returns status code even for HTTP errors.
    """
    try:
        ctx = SSL_CTX if url.startswith("https") else None
        resp = urllib.request.urlopen(url, timeout=timeout, context=ctx)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode() if e.fp else ""
    except Exception as e:
        return None, str(e)


def wait_for_nginx():
    """Wait for nginx to be ready."""
    for _ in range(MAX_RETRIES):
        status, _ = fetch(f"https://{NGINX_HOST}:443/", timeout=2)
        if status == 200:
            return True
        time.sleep(1)
    return False


def test_http_redirect():
    """ Test port 8080 redirects to HTTPS (301)."""
    # Use low-level request to check redirect without following
    import http.client
    conn = http.client.HTTPConnection(NGINX_HOST, 8080, timeout=5)
    conn.request("GET", "/")
    resp = conn.getresponse()
    conn.close()
    assert resp.status == 301, f"Expected 301, got {resp.status}"
    print("Port 8080: PASS (301 redirect)")


def test_https_endpoint():
    """Test port 443 returns 200 with HTML content."""
    status, body = fetch(f"https://{NGINX_HOST}:443/")
    assert status == 200, f"Expected 200, got {status}"
    assert "Hello from Nginx" in body, "Missing expected content"
    print("Port 443: PASS (HTTPS 200 OK)")


def test_error_endpoint():
    """Test port 8081 returns 403 error."""
    status, _ = fetch(f"http://{NGINX_HOST}:8081/")
    assert status == 403, f"Expected 403, got {status}"
    print("Port 8081: PASS (403 Forbidden)")


def test_rate_limiting():
    """Test rate limiting returns 429 when exceeded."""
    url = f"https://{NGINX_HOST}:443/"
    
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
    
    tests = [test_http_redirect, test_https_endpoint, test_error_endpoint, test_rate_limiting]
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
