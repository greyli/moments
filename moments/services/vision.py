import os
import requests

AZ_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT", "").rstrip("/")
AZ_KEY = os.getenv("AZURE_VISION_KEY")

def analyze_image(image_bytes: bytes) -> dict:
    """
    Returns {"caption": str|None, "labels": [str,...]}.
    Soft-fails (returns empty) if no keys or API error.
    """
    if not AZ_ENDPOINT or not AZ_KEY:
        return {"caption": None, "labels": []}

    url = f"{AZ_ENDPOINT}/computervision/imageanalysis:analyze"
    params = {"api-version": "2023-10-01", "features": "caption,tags"}
    headers = {
        "Ocp-Apim-Subscription-Key": AZ_KEY,
        "Content-Type": "application/octet-stream",
    }
    try:
        resp = requests.post(url, params=params, headers=headers, data=image_bytes, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return {"caption": None, "labels": []}

    caption = None
    labels = []
    cr = data.get("captionResult") or {}
    if cr.get("text"):
        caption = cr["text"]

    tr = data.get("tagsResult") or {}
    vals = tr.get("values") or []
    labels = [t.get("name") for t in vals if t.get("name")]

    return {"caption": caption, "labels": labels}
