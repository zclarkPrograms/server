import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import json
import praw
import re

PORT = 8000

LIMIT = 100


def getLinks(subreddit: str, num_posts: int = LIMIT) -> list[str]:
    with open("env.json", "r") as f:
        info = json.load(f)

    reddit = praw.Reddit(
        client_id=info["client_id"], client_secret=info["client_secret"], user_agent=info["user_agent"])

    subreddit = reddit.subreddit(subreddit)

    posts = subreddit.hot(limit=LIMIT)

    return [post.url for post in posts if re.search(r".*\.(png|jpg|gif|jpeg)", post.url)][:num_posts]


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if 'subreddit' in query_params:
            subreddit = query_params['subreddit'][0]
            num_posts = 20
            if 'num_posts' in query_params:
                try:
                    num_posts = int(query_params['num_posts'][0])
                except ValueError:
                    print("Invalid value for parameter 'limit'")

            links = getLinks(subreddit, num_posts)
            links = [re.sub(r"\.gifv$", ".gif", link) for link in links]
            response = {"subreddit": subreddit, "links": links}
            self.send_full_response(200, response)
        else:
            response = {"error": 'Missing "subreddit" parameter'}
            self.send_full_response(400, response)

    def send_full_response(self, code, response):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())


httpd = socketserver.TCPServer(("", PORT), RequestHandler)

print(f"Serving on port {PORT}")
httpd.serve_forever()
