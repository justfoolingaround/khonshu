import random
from datetime import datetime

import httpx
import keyboard
import yarl

from khonshu.webauth.browser import iter_raw_cookies_firefox

URL = "https://www.animeout.xyz/"
RETRY = 10.0


def get_browser_user_agent(port, url, stdout_func=print):

    import logging
    import threading
    from queue import Queue

    import werkzeug
    from werkzeug.serving import make_server

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.DEBUG)

    redirect_url = f"http://127.0.0.1:{port}/"

    token_awaiter = Queue()

    @werkzeug.Request.application
    def response_handler(request: werkzeug.Request):

        user_agent = request.headers.get("User-Agent")

        token_awaiter.put(user_agent)

        return werkzeug.Response(None, 302, {"Location": url})

    client_fetching_server = make_server("localhost", port, response_handler)
    local_thread = threading.Thread(target=client_fetching_server.serve_forever)

    local_thread.start()

    stdout_func(f"In your browser, proceed to: {redirect_url}{random.randint(0, 1000)}")

    token = token_awaiter.get(block=True)
    client_fetching_server.shutdown()

    local_thread.join()

    return token


def fetch_cookie(url, *, cookie_name="cf_clearance"):

    parsed_url = yarl.URL(url)

    generic_host = parsed_url.host.removeprefix("www")

    utc_now = datetime.utcnow()

    for cookie_data in iter_raw_cookies_firefox(
        sql_where=f"host={generic_host!r} and name={cookie_name!r} and expiry > {utc_now.timestamp()}",
    ):
        return cookie_data


user_agent = get_browser_user_agent(8080, URL)

print(f"Make sure you can load {URL!r} in your browser, then press enter to continue.")
keyboard.wait("enter", suppress=True, trigger_on_release=True)

cookies = fetch_cookie(URL)

headers = {
    "User-Agent": user_agent,
    "Cookie": f"cf_clearance={cookies['data']['value']}",
}


print(
    httpx.get(
        URL,
        headers=headers,
    )
)

print(headers)
