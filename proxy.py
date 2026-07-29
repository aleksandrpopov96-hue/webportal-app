from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import ssl
import re

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def proxy_fetch(self, url):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36')
        req.add_header('Accept', '*/*')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        return urllib.request.urlopen(req, timeout=15, context=ctx)

    def encode_url(self, url):
        return '/proxy?url=' + urllib.parse.quote(url, safe='')

    def get_nav_script(self, origin):
        return (
            '<script>'
            '(function(){'
            'var O="' + origin + '",P="/proxy?url=";'
            'function p(u){return u.indexOf(P)===0?u:P+encodeURIComponent(u)}'
            'document.addEventListener("click",function(e){'
            'var a=e.target.closest("a");'
            'if(!a||!a.href||a.protocol==="javascript:")return;'
            'var h=a.href;'
            'if(a.getAttribute("target")==="_blank")return;'
            'if(h.indexOf(O)===0){'
            'e.preventDefault();location.href=p(h)'
            '}else if(h.indexOf(location.origin)===0&&h.indexOf(P)!==0){'
            'e.preventDefault();location.href=p(h)'
            '}'
            '})'
            '})()'
            '</script>'
        )

    def rewrite_html(self, html, origin):
        def rewrite_attr(match):
            prefix = match.group(1)
            quote = match.group(2)
            val = match.group(3)
            if val.startswith('/proxy?') or val.startswith('http') or val.startswith('data:') or val.startswith('#') or val.startswith('javascript:'):
                return match.group(0)
            if val.startswith('//'):
                return match.group(0)
            if val.startswith('/'):
                full = origin + val
            else:
                full = origin + '/' + val
            return prefix + quote + self.encode_url(full) + quote

        html = re.sub(r'((?:href|src|action|poster|srcset)\s*=\s*)(["\'])(/[^"\']*?)\2', rewrite_attr, html, flags=re.IGNORECASE)

        html = re.sub(r'url\(\s*["\']?\s*(/[^)"\']*)\s*["\']?\s*\)', lambda m: 'url(' + self.encode_url(origin + m.group(1)) + ')', html)

        nav_script = self.get_nav_script(origin)
        html = html.replace('</head>', nav_script + '</head>', 1)

        return html

    def rewrite_css(self, css, origin):
        def rewrite_url(match):
            val = match.group(1)
            if val.startswith('/proxy?') or val.startswith('http') or val.startswith('data:'):
                return match.group(0)
            if val.startswith('//'):
                return match.group(0)
            if val.startswith('/'):
                full = origin + val
            else:
                return match.group(0)
            return 'url(' + self.encode_url(full) + ')'

        return re.sub(r'url\(\s*["\']?\s*([^)"\']*)\s*["\']?\s*\)', rewrite_url, css)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        url = params.get('url', [''])[0]

        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing url parameter')
            return

        try:
            resp = self.proxy_fetch(url)
            content = resp.read()
            content_type = ''
            for key, val in resp.getheaders():
                if key.lower() == 'content-type':
                    content_type = val.lower()

            parsed_url = urllib.parse.urlparse(url)
            origin = parsed_url.scheme + '://' + parsed_url.netloc

            if 'text/html' in content_type:
                html = content.decode('utf-8', errors='replace')
                html = self.rewrite_html(html, origin)
                content = html.encode('utf-8')
            elif 'text/css' in content_type:
                css = content.decode('utf-8', errors='replace')
                css = self.rewrite_css(css, origin)
                content = css.encode('utf-8')

            self.send_response(resp.getcode())
            skip = {'x-frame-options', 'content-security-policy', 'x-xss-protection',
                     'transfer-encoding', 'connection'}
            for key, val in resp.getheaders():
                if key.lower() not in skip:
                    self.send_header(key, val)
            self.end_headers()
            self.wfile.write(content)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

HTTPServer(('127.0.0.1', 8888), ProxyHandler).serve_forever()
