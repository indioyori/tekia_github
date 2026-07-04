# TEKIA — Código Fuente Completo
## Sistema Soberano de Investigación · FronterIA-Lab · Yoremnokki

---

## app/main.py

```python
import warnings; warnings.filterwarnings("ignore")
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import init_db, get_db
from .services.rag_service import _get_model
from .services.search_service import SearchService
from .routers.rag import router as rag_router
from .routers.notes import router as notes_router
from .routers.alerts import router as alerts_router

app = FastAPI(title="TEKIA", version="2.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(rag_router)
app.include_router(notes_router)
app.include_router(alerts_router)

@app.on_event("startup")
async def startup():
    init_db()
    _get_model()

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/rag")
def investigar(request: Request):
    return templates.TemplateResponse("rag.html", {"request": request})

@app.get("/notes")
def cuaderno(request: Request):
    return templates.TemplateResponse("notes.html", {"request": request})

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0"}

@app.get("/api/search/")
def unified_search(q: str, types: str = "documents,notes", db: Session = Depends(get_db)):
    svc = SearchService(db)
    results = []
    if "documents" in types: results += svc.search_documents(q)
    if "notes" in types: results += svc.search_notes(q)
    return results
```

---

## app/config.py

```python
from pathlib import Path

BASE_DIR       = Path(__file__).parent.parent
DATA_DIR       = BASE_DIR / "data"
DOCUMENTS_DIR  = DATA_DIR / "documents"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
KEYS_DIR       = BASE_DIR / "keys"
DB_PATH        = DATA_DIR / "tekia.db"
BIAS_VOCAB_DIR = BASE_DIR / "bias_vocab"
MODELS_DIR     = BASE_DIR / "models"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
```

---

## app/routers/rag.py — endpoint search_web con bias_vocab

```python
@router.get("/search-web/")
def search_web(q: str, max_results: int = 8):
    import requests, urllib.parse
    from bs4 import BeautifulSoup
    from app.config import BIAS_VOCAB_DIR

    HEG_DOMAINS = {
        "reforma.com","eleconomista.com.mx","milenio.com","eluniversal.com.mx",
        "expansion.mx","forbes.com.mx","reuters.com","bbc.com","nytimes.com",
        "larazon.com.mx","excelsior.com.mx","informador.mx","jornada.com.mx",
        "sinembargo.mx","proceso.com.mx","aristeguinoticias.com",
        "animalpolitico.com","elfinanciero.com.mx","heraldo.mx",
    }
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": q},
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
            timeout=15
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        heg_v = set((BIAS_VOCAB_DIR/"hegemonic_terms.txt").read_text().lower().split()) \
                if (BIAS_VOCAB_DIR/"hegemonic_terms.txt").exists() else set()
        sit_v = set((BIAS_VOCAB_DIR/"situated_terms.txt").read_text().lower().split()) \
                if (BIAS_VOCAB_DIR/"situated_terms.txt").exists() else set()
        results = []
        for item in soup.select(".web-result")[:max_results]:
            a    = next((l for l in item.select("a[href*='uddg']") if len(l.get_text(strip=True)) > 10), None)
            snip = item.select_one(".result__snippet")
            if not a: continue
            raw  = ("https:" + a["href"]) if a["href"].startswith("//") else a["href"]
            url  = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query).get("uddg", [raw])[0]
            dom  = url.replace("https://","").replace("http://","").split("/")[0].replace("www.","")
            txt  = (a.get_text(strip=True) + " " + (snip.get_text(strip=True) if snip else "")).lower()
            h    = sum(1 for w in heg_v if w in txt)
            s    = sum(1 for w in sit_v if w in txt)
            auto = "hegemonic" if (any(d in dom for d in HEG_DOMAINS) or h > s) else "situated"
            results.append({
                "title": a.get_text(strip=True),
                "href": url,
                "body": snip.get_text(strip=True) if snip else "",
                "auto_type": auto
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]
```

---

## app/services/grieta_service.py

```python
"""
GrietaService — Análisis cruzado HEG/SIT
Resumen LexRank · Léxico TF-IDF · Silencios · Actores spaCy · Cronología · Divergencia coseno
Sin LLM. Sin nube.
"""
import re
from pathlib import Path
from sqlalchemy.orm import Session
from app.config import BIAS_VOCAB_DIR
from app.models.document import Document


class GrietaService:
    def __init__(self, db: Session):
        self.db = db
        self._nlp = None
        self._load_vocab()

    def _load_vocab(self):
        heg = BIAS_VOCAB_DIR / "hegemonic_terms.txt"
        sit = BIAS_VOCAB_DIR / "situated_terms.txt"
        self.heg_vocab = set(heg.read_text(encoding="utf-8").splitlines()) if heg.exists() else set()
        self.sit_vocab = set(sit.read_text(encoding="utf-8").splitlines()) if sit.exists() else set()

    def _nlp_model(self):
        if self._nlp is None:
            import spacy
            self._nlp = spacy.load("es_core_news_md")
        return self._nlp

    def _get_text(self, doc_id):
        doc = self.db.query(Document).get(doc_id)
        if not doc or not doc.file_path: return ""
        p = Path(doc.file_path)
        if not p.exists(): return ""
        if p.suffix == ".pdf":
            import fitz
            return "\n".join(page.get_text() for page in fitz.open(str(p)))
        return p.read_text(encoding="utf-8", errors="ignore")

    def _summarize(self, texts):
        if not texts: return ""
        combined = " ".join(t[:20000] for t in texts[:4])
        try:
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            from sumy.summarizers.lex_rank import LexRankSummarizer
            parser = PlaintextParser.from_string(combined, Tokenizer("spanish"))
            sents = LexRankSummarizer()(parser.document, 5)
            return " ".join(str(s) for s in sents)
        except Exception:
            return combined[:800]

    def _tfidf_top(self, texts, n=40):
        if not texts: return []
        from sklearn.feature_extraction.text import TfidfVectorizer
        try:
            vec = TfidfVectorizer(max_features=300, min_df=1)
            mat = vec.fit_transform(texts)
            scores = mat.toarray().mean(axis=0)
            terms = vec.get_feature_names_out()
            return [t for t, _ in sorted(zip(terms, scores), key=lambda x: -x[1]) if len(t) > 3][:n]
        except Exception:
            return []

    def _lexicon(self, texts_heg, texts_sit):
        heg = set(self._tfidf_top(texts_heg, 50))
        sit = set(self._tfidf_top(texts_sit, 50))
        return {"exclusivo_heg": sorted(heg - sit)[:20], "exclusivo_sit": sorted(sit - heg)[:20], "compartido": sorted(heg & sit)[:15]}

    def _silencios(self, texts_heg, texts_sit):
        txt_heg = " ".join(texts_heg).lower()
        txt_sit = " ".join(texts_sit).lower()
        return {
            "heg_silencia": [t for t in sorted(self.sit_vocab) if t.lower() not in txt_heg][:15],
            "sit_silencia": [t for t in sorted(self.heg_vocab) if t.lower() not in txt_sit][:15],
        }

    def _actores(self, texts_heg, texts_sit):
        nlp = self._nlp_model()
        def ent_verbs(texts):
            ev = {}
            for text in texts[:2]:
                doc = nlp(text[:40000])
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "PER"):
                        verbs = [t.lemma_ for t in ent.sent if t.pos_ == "VERB"]
                        ev.setdefault(ent.text.strip(), []).extend(verbs)
            return {k: list(set(v))[:5] for k, v in list(ev.items())[:15]}
        heg_ev = ent_verbs(texts_heg)
        sit_ev = ent_verbs(texts_sit)
        shared = set(heg_ev) & set(sit_ev)
        return [{"actor": a, "heg_verbos": heg_ev[a], "sit_verbos": sit_ev[a]} for a in list(shared)[:8]]

    def _cronologia(self, texts_heg, texts_sit):
        import dateparser
        pat = r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4}\b|\b\d{4}\b'
        def events(texts, src):
            result = []
            for text in texts[:2]:
                for m in re.finditer(pat, text, re.IGNORECASE):
                    try:
                        parsed = dateparser.parse(m.group(), languages=["es"])
                        if parsed and 2000 <= parsed.year <= 2030:
                            s, e = max(0, m.start()-80), min(len(text), m.end()+80)
                            result.append({"year": parsed.year, "ctx": text[s:e].replace("\n"," ").strip()[:120], "src": src})
                    except Exception:
                        pass
            return result
        all_ev = events(texts_heg, "heg") + events(texts_sit, "sit")
        by_year = {}
        for ev in all_ev:
            by_year.setdefault(ev["year"], {"heg":[],"sit":[]})
            by_year[ev["year"]][ev["src"]].append(ev["ctx"])
        return [{"year": y, "heg": by_year[y]["heg"][:2], "sit": by_year[y]["sit"][:2]} for y in sorted(by_year)[-15:]]

    def _divergencia(self, texts_heg, texts_sit):
        if not texts_heg or not texts_sit: return 0.0
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        try:
            mat = TfidfVectorizer(max_features=500).fit_transform([" ".join(texts_heg), " ".join(texts_sit)])
            return round(1.0 - float(cosine_similarity(mat[0:1], mat[1:2])[0][0]), 3)
        except Exception:
            return 0.0

    def generar(self, doc_ids_heg, doc_ids_sit):
        texts_heg = [t for did in doc_ids_heg if (t := self._get_text(did))]
        texts_sit = [t for did in doc_ids_sit if (t := self._get_text(did))]
        return {
            "resumen_heg": self._summarize(texts_heg),
            "resumen_sit": self._summarize(texts_sit),
            "lexicon":     self._lexicon(texts_heg, texts_sit),
            "silencios":   self._silencios(texts_heg, texts_sit),
            "actores":     self._actores(texts_heg, texts_sit),
            "cronologia":  self._cronologia(texts_heg, texts_sit),
            "divergencia": self._divergencia(texts_heg, texts_sit),
        }
```


---

## app/templates/rag.html — Página INVESTIGAR

```html
{% extends "base.html" %}
{% block title %}Investigar{% endblock %}
{% block page %}investigar{% endblock %}
{% block nav_inv %}active{% endblock %}
{% block content %}

<div class="inv-header">
  <h1>Investigar</h1>
  <div class="search-bar">
    <input type="text" id="inv-query"
           placeholder="Tema de investigación: ej. GPO Ohuira amoniaco KfW..." autofocus>
    <input type="date" id="inv-from" title="Desde">
    <input type="date" id="inv-to"   title="Hasta">
    <button class="btn btn-jade" id="btn-buscar">Buscar</button>
  </div>
</div>

<div class="inv-content">

  <!-- Resultados HEG / SIT en dos columnas -->
  <div class="results-grid">
    <div class="results-col col-heg">
      <h3>Hegemónico</h3>
      <div id="results-heg">
        <div class="empty">Ingresa un tema para investigar</div>
      </div>
    </div>
    <div class="results-col col-sit">
      <h3>Situado</h3>
      <div id="results-sit"></div>
    </div>
  </div>

  <!-- LA GRIETA — generada automáticamente al descargar docs -->
  <div class="grieta-panel hidden" id="grieta-panel">
    <div class="grieta-header">
      <h2>La Grieta Epistémica</h2>
      <div class="flex gap-8 items-center">
        <span class="divergencia-badge" id="div-score">Divergencia: —</span>
        <div class="div-bar" style="width:120px">
          <div class="div-fill" id="div-bar-fill" style="width:0%"></div>
        </div>
      </div>
    </div>
    <div class="grieta-body" id="grieta-body">
      <div class="loading" style="padding:20px">Analizando corpus…</div>
    </div>
    <div class="grieta-actions">
      <button class="btn btn-jade"   onclick="abrirEnCuaderno()">→ Abrir en Cuaderno</button>
      <button class="btn btn-copper" onclick="abrirAlertaModal()">⏰ Alerta de seguimiento</button>
    </div>
  </div>

</div>
{% endblock %}
```

---

## app/templates/notes.html — Cuaderno (tipo Obsidian/Upnote)

```html
{% extends "base.html" %}
{% block title %}Cuaderno{% endblock %}
{% block page %}cuaderno{% endblock %}
{% block nav_notas %}active{% endblock %}
{% block content %}

<div class="notes-layout">

  <!-- Panel izquierdo: lista de notas -->
  <div class="notes-list-panel">
    <div class="nlp-header">
      <h2>Cuaderno</h2>
      <div class="nlp-search">
        <input type="text" id="note-search" placeholder="Buscar notas…">
      </div>
    </div>
    <div class="note-items" id="notes-list">
      <div class="loading" style="padding:16px">Cargando…</div>
    </div>
    <div class="nlp-new-btn">
      <button class="btn btn-jade" style="width:100%" id="btn-new-note">+ Nueva nota</button>
    </div>
  </div>

  <!-- Panel derecho: editor -->
  <div class="editor-panel hidden" id="editor-panel">

    <!-- Metadatos -->
    <div class="editor-meta">
      <input class="note-title-input" type="text" id="note-title" placeholder="Título…" required>
      <input class="note-theme-input" type="text" id="note-theme" placeholder="Tema">
      <input class="note-tags-input"  type="text" id="note-tags"  placeholder="tags, separados, por, coma">
    </div>

    <!-- Toolbar formato Markdown -->
    <div class="editor-toolbar">
      <button class="tb-btn" data-fmt="bold"   title="Negrita">B</button>
      <button class="tb-btn" data-fmt="italic" title="Cursiva"><em>I</em></button>
      <button class="tb-btn" data-fmt="h2"     title="Título 2">H2</button>
      <button class="tb-btn" data-fmt="h3"     title="Título 3">H3</button>
      <div class="tb-sep"></div>
      <button class="tb-btn" data-fmt="strike" title="Tachado"><s>S</s></button>
      <button class="tb-btn" data-fmt="link"   title="Enlace">⛓</button>
      <button class="tb-btn" data-fmt="quote"  title="Cita">"</button>
      <div class="tb-sep"></div>
      <button class="tb-btn" data-fmt="ul"     title="Lista">•</button>
      <button class="tb-btn" data-fmt="ol"     title="Numerada">1.</button>
      <button class="tb-btn" data-fmt="code"   title="Código">&lt;/&gt;</button>
    </div>

    <!-- Tabs Editar / Vista previa -->
    <div class="editor-tabs">
      <div class="editor-tab active" data-tab="edit">Editar</div>
      <div class="editor-tab"        data-tab="preview">Vista previa</div>
    </div>

    <div class="editor-body">
      <textarea class="note-textarea" id="note-content"
                placeholder="Escribe en Markdown…"></textarea>
      <div class="note-preview hidden" id="panel-preview"></div>
    </div>

    <!-- Footer: exportación + acciones -->
    <div class="editor-footer">
      <div class="editor-footer-left">
        <button class="btn btn-ghost btn-sm" id="btn-export-pdf">PDF</button>
        <button class="btn btn-ghost btn-sm" id="btn-export-md">Markdown</button>
        <button class="btn btn-ghost btn-sm" id="btn-export-zenodo">Zenodo</button>
        <button class="btn btn-danger btn-sm hidden" id="btn-delete-note">Eliminar</button>
      </div>
      <div class="editor-footer-right">
        <button class="btn btn-jade" id="btn-save-note">Guardar</button>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

---

## Comandos de arranque

```bash
cd ~/tekia
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES uvicorn app.main:app --port 8100
# Abrir: http://127.0.0.1:8100
```

## Estado del sistema

| Módulo | Archivo | Estado |
|--------|---------|--------|
| Base y entorno | app/main.py, app/config.py, app/database.py | ✅ |
| Modelos ORM | app/models/*.py | ✅ |
| Crypto | app/services/crypto_service.py | ✅ |
| RAG service | app/services/rag_service.py | ✅ |
| Note service | app/services/note_service.py | ✅ |
| Alert service | app/services/alert_service.py | ✅ |
| Search service | app/services/search_service.py | ✅ |
| Integration | app/services/integration.py | ✅ |
| Grieta service | app/services/grieta_service.py | ✅ |
| Routers | app/routers/*.py | ✅ |
| UI templates | app/templates/*.html | ✅ |
| Clasificación HEG/SIT | Ahora usa bias_vocab + dominios | ✅ fix aplicado |

## Problema pendiente

La Grieta se genera solo cuando hay documentos descargados de AMBOS tipos (HEG + SIT).
Flujo correcto:
1. Buscar tema → resultados aparecen en columnas
2. Clic [+ Hegemónico] en fuentes hegemónicas
3. Clic [+ Situado] en fuentes situadas
4. Grieta aparece automáticamente
