import io
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

os.environ.pop("OPENAI_API_KEY", None)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config import Config
Config.OPENAI_API_KEY = ""
from app import create_app

app = create_app()
client = app.test_client()

results = []

def add(name, resp):
    results.append({"test": name, "status_code": resp.status_code, "json": resp.get_json()})

# 1. Health check
add("health", client.get("/api/health"))

# 2. Language list
add("languages", client.get("/api/translate/languages"))

# 3. Language detection examples
for name, payload in [
    ("detect_english", {"text": "Hello, how are you?"}),
    ("detect_romanized_hindi", {"text": "kem cho"}),
    ("detect_french", {"text": "Bonjour tout le monde"}),
]:
    add(name, client.post("/api/translate/detect", json=payload))

# 4. Translation examples
for name, payload in [
    ("translate_en_to_es", {"text": "Hello world", "target_lang": "es", "tone": "professional"}),
    ("translate_romanized_hindi", {"text": "kem cho", "source_lang": "auto", "target_lang": "en", "tone": "friendly"}),
    ("translate_spanish_to_en", {"text": "¿Cómo estás?", "source_lang": "auto", "target_lang": "en", "tone": "casual", "save_history": True}),
]:
    add(name, client.post("/api/translate/translate", json=payload))

# 5. Slang endpoints
add("slang_modes", client.get("/api/slang/modes"))
add("slang_glossary", client.get("/api/slang/glossary?limit=10"))
for name, payload in [
    ("slang_genz_to_plain", {"text": "bruh that\'s bussin fr", "mode": "genz_to_plain", "use_ai": False}),
    ("slang_plain_to_genz", {"text": "I am going to the movies", "mode": "plain_to_genz", "use_ai": False, "save_history": True}),
]:
    add(name, client.post("/api/slang/translate", json=payload))

# 6. AI endpoints
add("grammar_correction", client.post("/api/ai/grammar", json={"text": "I has a cat. She dont like it."}))
add("summarize_translate", client.post("/api/ai/summarize-translate", json={"text": "Python is a popular programming language. It is used for web development, data science, automation, and scripting. Many developers enjoy its clean syntax.", "target_lang": "es"}))

# 7. Document translation with txt file
text_file = io.BytesIO(b"This is a small document. It should translate correctly.")
text_file.name = "sample.txt"
add("document_translate_txt", client.post(
    "/api/document/translate",
    content_type="multipart/form-data",
    data={"document": (text_file, "sample.txt"), "target_lang": "es"},
))

# 8. OCR endpoints with generated image
img = Image.new("RGB", (450, 100), color=(255, 255, 255))
draw = ImageDraw.Draw(img)
draw.text((10, 10), "Test OCR", fill=(0, 0, 0))

for name, endpoint in [
    ("ocr_extract", "/api/ocr/extract"),
    ("ocr_translate_image", "/api/ocr/translate-image"),
]:
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    img_bytes.name = "ocr_test.png"
    data = {"image": (img_bytes, "ocr_test.png"), "lang": "eng"}
    if endpoint.endswith("translate-image"):
        data.update({"target_lang": "es", "source_lang": "auto"})
    add(name, client.post(endpoint, content_type="multipart/form-data", data=data))

# 9. History CRUD
client.delete("/api/history/clear")
add("history_empty", client.get("/api/history/"))
add("history_create", client.post("/api/history/", json={
    "original_text": "Testing history feature.",
    "translated_text": "Historial de prueba.",
    "source_lang": "en",
    "target_lang": "es",
}))
add("history_list", client.get("/api/history/"))
item_id = results[-1]["json"]["history"][0]["id"] if results[-1]["status_code"] == 200 and results[-1]["json"]["history"] else None
if item_id:
    add("history_favorite", client.patch(f"/api/history/{item_id}/favorite"))
    add("history_search", client.get("/api/history/?search=history"))
    add("history_delete", client.delete(f"/api/history/{item_id}"))
add("history_clear", client.delete("/api/history/clear"))

summary = []
for item in results:
    s = {
        "test": item["test"],
        "status_code": item["status_code"],
    }
    body = item.get("json")
    if isinstance(body, dict):
        if "translated_text" in body:
            s["translated_text"] = body["translated_text"]
        if "detected_lang" in body:
            s["detected_lang"] = body["detected_lang"]
        if "original_text" in body and item["test"].startswith("document_"):
            s["original_text_snippet"] = body["original_text"][:50]
        if "error" in body:
            s["error"] = body["error"]
        if "history" in body:
            s["history_count"] = len(body["history"])
        if "glossary" in body:
            s["glossary_count"] = len(body["glossary"])
        if "languages" in body:
            s["language_count"] = len(body["languages"])
    summary.append(s)
print(json.dumps(summary, indent=2, ensure_ascii=False))
