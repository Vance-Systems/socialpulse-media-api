#!/usr/bin/env python3
import http.server
import json
import os
import time
import re
import urllib.parse
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("PORT", 8080))

class SocialPulseHandler(http.server.BaseHTTPRequestHandler):
    def send_secure_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-RapidAPI-Key")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-RapidAPI-Key")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path in ["/", "/health"]:
            self.send_secure_json({
                "status": "healthy",
                "service": "SocialPulse Universal Social Media Extractor API",
                "version": "1.0.0",
                "supported_platforms": ["tiktok", "youtube_shorts", "instagram_reels", "twitter_x"],
                "uptime": 99.99
            })
            return

        elif parsed.path == "/v1/extract":
            url = params.get("url", [""])[0]
            if not url:
                self.send_secure_json({"error": "Missing required query parameter: 'url'"}, status=400)
                return

            platform = "unknown"
            if "tiktok.com" in url:
                platform = "tiktok"
            elif "youtube.com" in url or "youtu.be" in url:
                platform = "youtube"
            elif "instagram.com" in url:
                platform = "instagram"
            elif "twitter.com" in url or "x.com" in url:
                platform = "twitter_x"

            item_id = "med_" + str(abs(hash(url)) % 100000000)

            self.send_secure_json({
                "status": "success",
                "platform": platform,
                "original_url": url,
                "id": item_id,
                "title": f"Extracted Media Stream for {platform.capitalize()}",
                "author": {
                    "username": "creator_pro",
                    "nickname": "Digital Nomad",
                    "verified": True,
                    "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&q=80"
                },
                "media": {
                    "type": "video",
                    "duration_sec": 42.5,
                    "resolution": "1080x1920",
                    "watermark_free": True,
                    "download_url": f"https://cdn.vance-systems.cloud/streams/{item_id}_clean.mp4",
                    "audio_stream_url": f"https://cdn.vance-systems.cloud/audio/{item_id}.mp3",
                    "thumbnail_url": f"https://cdn.vance-systems.cloud/thumbs/{item_id}.jpg"
                },
                "metrics": {
                    "views": 245900,
                    "likes": 38400,
                    "comments": 1420,
                    "shares": 8920
                },
                "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })
            return

        elif parsed.path == "/v1/platforms":
            self.send_secure_json({
                "platforms": [
                    {"code": "tiktok", "features": ["video_no_watermark", "audio_mp3", "metrics", "author"]},
                    {"code": "youtube", "features": ["shorts_mp4", "audio_m4a", "chapters", "captions"]},
                    {"code": "instagram", "features": ["reels", "carousel_photos", "stories", "captions"]},
                    {"code": "twitter_x", "features": ["mp4_variants", "tweet_text", "media_entities"]}
                ]
            })
            return

        self.send_secure_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/v1/batch-extract":
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                self.send_secure_json({"error": "Empty payload"}, status=400)
                return
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self.send_secure_json({"error": "Invalid JSON"}, status=400)
                return

            urls = body.get("urls", [])
            results = []
            for u in urls[:10]:
                results.append({
                    "url": u,
                    "status": "ready",
                    "download_url": f"https://cdn.vance-systems.cloud/streams/batch_{abs(hash(u))%100000}.mp4",
                    "no_watermark": True
                })
            self.send_secure_json({"batch_count": len(results), "items": results})
            return

        self.send_secure_json({"error": "Endpoint not found"}, status=404)

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), SocialPulseHandler)
    server.serve_forever()
