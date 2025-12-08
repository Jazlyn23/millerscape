import requests
from urllib.parse import urlparse, urljoin
from flask import Flask, request, Response, render_template_string

app = Flask(__name__)

HTML_FORM = '''
<!DOCTYPE html>
<html>
  <head>
    <title>Web Proxy - millerscape</title>
    <style>
        body { font-family: Arial; margin: 28px }
        input[type="text"] { width: 400px; padding: 6px }
        button { padding: 6px }
    </style>
  </head>
  <body>
    <h2>Proxy Browser</h2>
    <form method="GET" action="/">
      <input type="text" name="url" placeholder="Enter a URL (e.g. https://example.com)" required>
      <button type="submit">Go</button>
    </form>
    {% if error %}
      <p style="color:red;">{{ error }}</p>
    {% endif %}
  </body>
</html>
'''

def rewrite_html(html, base_url):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    tags = [("a", "href"), ("img", "src"), ("script", "src"), ("link", "href")]
    for tag, attr in tags:
        for t in soup.find_all(tag):
            url = t.get(attr)
            if url:
                if url.startswith("http"):
                    t[attr] = "/proxy?url=" + url
                elif url.startswith("//"):
                    t[attr] = "/proxy?url=http:" + url
                elif url.startswith("/"):
                    domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
                    t[attr] = "/proxy?url=" + urljoin(domain, url)
                else:
                    t[attr] = "/proxy?url=" + urljoin(base_url, url)
    return str(soup)

@app.route("/", methods=["GET"])
def index():
    url = request.args.get("url")
    if not url:
        return render_template_string(HTML_FORM)
    return '''
        <iframe src="/proxy?url={}" width="100%" height="800" style="border:none"></iframe>
        <br>
        <a href="/">Go back</a>
    '''.format(url)

@app.route("/proxy", methods=["GET"])
def proxy():
    url = request.args.get("url")
    if not url:
        return render_template_string(HTML_FORM, error="No URL provided")
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=9)
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            rewritten = rewrite_html(resp.text, url)
            return Response(rewritten, content_type=content_type)
        elif "image" in content_type or "javascript" in content_type or "css" in content_type:
            return Response(resp.content, content_type=content_type)
        else:
            return Response(resp.content, content_type=content_type)
    except Exception as e:
        return render_template_string(HTML_FORM, error=f"Error: {e}")

if __name__ == "__main__":
    app.run(debug=True)
