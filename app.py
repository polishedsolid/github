from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request, send_file

from downloader.extractor import FetchError
from downloader.zipper import build_zip

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return jsonify({"error": "Only http:// and https:// URLs are supported"}), 400

    try:
        zip_buf, count = build_zip(url)
    except FetchError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        app.logger.exception("Unexpected error building ZIP")
        return jsonify({"error": "An unexpected error occurred"}), 500

    if count == 0:
        return jsonify({"error": "No qualifying images found on that page"}), 404

    hostname = parsed.hostname or "images"
    filename = f"{hostname}-images.zip"

    zip_buf.seek(0)
    return send_file(
        zip_buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
