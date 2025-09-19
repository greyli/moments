import os
import requests

AZ_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT", "").rstrip("/")
AZ_KEY = os.getenv("AZURE_VISION_KEY")

def _post(url: str, params: dict, body: bytes):
    headers = {
        "Ocp-Apim-Subscription-Key": AZ_KEY,
        "Content-Type": "application/octet-stream",
    }
    r = requests.post(url, params=params, headers=headers, data=body, timeout=20)
    r.raise_for_status()
    return r.json()

def analyze_image(image_bytes: bytes) -> dict:
    """
    Returns {"caption": str|None, "labels": [str,...]}.

    Strategy:
      - Get 4.0 TAGS independently (best-effort).
      - Get CAPTION: try 4.0 caption only; if unsupported/error -> 3.2 describe.
    """
    if not AZ_ENDPOINT or not AZ_KEY:
        return {"caption": None, "labels": []}

    labels: list[str] = []
    caption: str | None = None

    # 1) TAGS via 4.0 (independent of caption)
    try:
        data_tags = _post(
            f"{AZ_ENDPOINT}/computervision/imageanalysis:analyze",
            {"api-version": "2023-10-01", "features": "tags"},
            image_bytes,
        )
        vals = ((data_tags or {}).get("tagsResult") or {}).get("values") or []
        labels = [t.get("name") for t in vals if t.get("name")]
    except Exception:
        # keep labels empty; continue with caption attempts
        labels = []

    # 2) CAPTION: try 4.0 caption only
    try:
        data_cap = _post(
            f"{AZ_ENDPOINT}/computervision/imageanalysis:analyze",
            {"api-version": "2023-10-01", "features": "caption"},
            image_bytes,
        )
        cap = (data_cap or {}).get("captionResult") or {}
        if cap.get("text"):
            caption = cap["text"]
    except Exception:
        # 3) Fallback to 3.2 Describe
        try:
            data32 = _post(
                f"{AZ_ENDPOINT}/vision/v3.2/describe",
                {"maxCandidates": "1", "language": "en"},
                image_bytes,
            )
            caps = ((data32 or {}).get("description") or {}).get("captions") or []
            if caps:
                caption = caps[0].get("text") or caption
        except Exception:
            pass

    return {"caption": caption, "labels": labels}
