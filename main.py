from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="Translate Backend", version="1.0.0")

# CORS cho frontend chạy Live Server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://nnkhlh376.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranslateReq(BaseModel):
    source_lang: str
    target_lang: str
    text: str


class TranslateResp(BaseModel):
    translated_text: str | None
    src: str | None = None
    dest: str | None = None
    error: str | None = None


def google_translate_raw(text: str, src: str, dest: str) -> tuple[str, str]:
    """
    Gọi trực tiếp endpoint translate.googleapis.com,
    trả về (translated_text, detected_source_lang)
    """
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": src,
        "tl": dest,
        "dt": "t",
        "q": text,
    }

    r = httpx.get(url, params=params, timeout=10)
    r.raise_for_status()  # nếu HTTP lỗi sẽ ném ngoại lệ

    data = r.json()
    # data[0] là list các segment [[ "xin chào", "hello", ... ], ...]
    translated = "".join(part[0] for part in data[0])
    detected_src = data[2] if len(data) > 2 and isinstance(data[2], str) else src
    return translated, detected_src


@app.post("/api/translate", response_model=TranslateResp)
def translate(req: TranslateReq):
    # Nếu cùng ngôn ngữ thì trả nguyên văn
    if req.source_lang == req.target_lang:
        return TranslateResp(
            translated_text=req.text,
            src=req.source_lang,
            dest=req.target_lang,
            error=None,
        )

    try:
        translated, detected_src = google_translate_raw(
            req.text, req.source_lang, req.target_lang
        )
        return TranslateResp(
            translated_text=translated,
            src=detected_src,
            dest=req.target_lang,
            error=None,
        )
    except Exception as e:
        # Trả lỗi về cho frontend hiển thị dòng đỏ
        return TranslateResp(
            translated_text=None,
            src=req.source_lang,
            dest=req.target_lang,
            error=str(e),
        )


@app.get("/api/health")
def health():
    return {"status": "ok"}


