# masters/views/media_proxy.py
import requests
from urllib.parse import urlparse
from django.http import StreamingHttpResponse, HttpResponseBadRequest

ALLOWED_VIDEO_HOSTS = {"www.w3schools.com", "your.cdn.com"}  # à compléter

def video_proxy(request):
    url = request.GET.get("url", "")
    if not url:
        return HttpResponseBadRequest("missing url")

    host = urlparse(url).netloc.lower()
    if host not in ALLOWED_VIDEO_HOSTS:
        return HttpResponseBadRequest("host not allowed")

    try:
        r = requests.get(url, stream=True, timeout=15, headers={"User-Agent":"ESFe/1.0"})
    except Exception:
        return HttpResponseBadRequest("upstream error")

    resp = StreamingHttpResponse(r.iter_content(chunk_size=64*1024),
                                 status=r.status_code, content_type=r.headers.get("Content-Type","video/mp4"))
    # autoriser ton front
    resp["Access-Control-Allow-Origin"] = "*"
    # permettre le seek
    if "Content-Length" in r.headers:
        resp["Content-Length"] = r.headers["Content-Length"]
    if "Accept-Ranges" in r.headers:
        resp["Accept-Ranges"] = r.headers["Accept-Ranges"]
    else:
        resp["Accept-Ranges"] = "bytes"
    return resp
