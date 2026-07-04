"""
Servicio RAG (Retrieval-Augmented Generation) para TEKIA.
Maneja descarga, indexación y análisis de documentos.
"""
import requests
import urllib.parse
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import fitz  # PyMuPDF
import re

from ..config import (
    HEG_DOMAINS, BIAS_VOCAB_DIR, HEGEMONIC_DIR, SITUATED_DIR,
    EMBEDDING_MODEL, MODELS_DIR, SEARXNG_ENABLED, SEARXNG_URL,
    GOOGLE_CSE_ENABLED, GOOGLE_CSE_API_KEY, GOOGLE_CSE_CX
)
from ..models import Document
from .crypto_service import crypto_service


class RAGService:
    """Servicio para descarga, almacenamiento e indexación de documentos."""
    
    def __init__(self, db: Session):
        self.db = db
        self._model = None
        self._load_bias_vocab()
    
    def _load_bias_vocab(self):
        """Carga los vocabulario de sesgo para clasificación HEG/SIT."""
        self.heg_vocab = set()
        self.sit_vocab = set()
        
        heg_file = BIAS_VOCAB_DIR / "hegemonic_terms.txt"
        sit_file = BIAS_VOCAB_DIR / "situated_terms.txt"
        
        if heg_file.exists():
            self.heg_vocab = set(
                heg_file.read_text(encoding="utf-8").lower().splitlines()
            )
        if sit_file.exists():
            self.sit_vocab = set(
                sit_file.read_text(encoding="utf-8").lower().splitlines()
            )
        
        # Términos por defecto si los archivos no existen
        if not self.heg_vocab:
            self.heg_vocab = {
                "desarrollo", "progreso", "modernización", "civilización",
                "crecimiento", "inversión", "mercado", "empresa", "gobierno",
                "seguridad", "estabilidad", "orden", "ley", "desarrollo sostenible"
            }
        if not self.sit_vocab:
            self.sit_vocab = {
                "resistencia", "autonomía", "soberanía", "despojo",
                "lucha", "comunidad", "pueblo", "indígena", "campesino",
                "derechos", "justicia", "liberación", "territorio", "agua"
            }
    
    def _get_model(self):
        """Carga el modelo de embeddings (lazy loading)."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            model_path = MODELS_DIR / EMBEDDING_MODEL
            if model_path.exists():
                self._model = SentenceTransformer(str(model_path))
            else:
                # Descargar modelo si no existe
                self._model = SentenceTransformer(EMBEDDING_MODEL)
                self._model.save(str(model_path))
        return self._model
    
    def _classify_document(self, url: str, title: str, snippet: str) -> str:
        """
        Clasifica un documento como 'hegemonic' o 'situated'.
        Prioridad: 1. Vocabulario de sesgo, 2. Dominio.
        """
        # Extraer dominio
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        domain = domain.replace("www.", "").lower()
        
        # Texto para análisis de vocabulario
        text = (title + " " + snippet).lower()
        
        # Contar términos de vocabulario
        heg_score = sum(1 for term in self.heg_vocab if term in text)
        sit_score = sum(1 for term in self.sit_vocab if term in text)
        
        # Clasificación por vocabulario (prioridad)
        if heg_score > sit_score:
            return "hegemonic"
        elif sit_score > heg_score:
            return "situated"
        
        # Clasificación por dominio (fallback)
        if domain in HEG_DOMAINS:
            return "hegemonic"
        else:
            return "situated"
    
    def search_web(self, query: str, max_results: int = 8) -> List[Dict]:
        """
        Busca en la web usando DuckDuckGo HTML o fallbacks.
        """
        results = []
        
        # Intentar con DuckDuckGo HTML primero
        try:
            results = self._search_duckduckgo(query, max_results)
            if results:
                return results
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
        
        # Fallback 1: SearXNG
        if SEARXNG_ENABLED:
            try:
                results = self._search_searxng(query, max_results)
                if results:
                    return results
            except Exception as e:
                print(f"SearXNG search failed: {e}")
        
        # Fallback 2: Google Custom Search
        if GOOGLE_CSE_ENABLED and GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX:
            try:
                results = self._search_google_cse(query, max_results)
                if results:
                    return results
            except Exception as e:
                print(f"Google CSE search failed: {e}")
        
        return [{"error": "No se pudo realizar la búsqueda. Verifica tu conexión o configura un fallback."}]
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        """Busca en DuckDuckGo HTML."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        params = {"q": query}
        
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params=params,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        for item in soup.select(".web-result")[:max_results]:
            # Extraer enlace
            a_tag = next(
                (l for l in item.select("a[href*='uddg']") 
                 if len(l.get_text(strip=True)) > 10),
                None
            )
            if not a_tag:
                continue
            
            # Extraer snippet
            snippet_tag = item.select_one(".result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            
            # Procesar URL
            raw_url = a_tag["href"]
            if raw_url.startswith("//"):
                raw_url = "https:" + raw_url
            
            # Extraer URL real de los parámetros uddg
            parsed = urllib.parse.urlparse(raw_url)
            url = urllib.parse.parse_qs(parsed.query).get("uddg", [raw_url])[0]
            
            # Extraer dominio
            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            domain = domain.replace("www.", "").lower()
            
            # Clasificar documento
            source_type = self._classify_document(url, a_tag.get_text(strip=True), snippet)
            
            results.append({
                "title": a_tag.get_text(strip=True),
                "href": url,
                "body": snippet,
                "auto_type": source_type,
                "domain": domain
            })
        
        return results
    
    def _search_searxng(self, query: str, max_results: int) -> List[Dict]:
        """Busca usando SearXNG."""
        params = {
            "q": query,
            "format": "json",
            "engines": "google,bing,duckduckgo",
            "pageno": 1
        }
        
        response = requests.get(f"{SEARXNG_URL}/search", params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get("results", [])[:max_results]:
            source_type = self._classify_document(
                item.get("url", ""),
                item.get("title", ""),
                item.get("content", "")
            )
            
            results.append({
                "title": item.get("title", ""),
                "href": item.get("url", ""),
                "body": item.get("content", ""),
                "auto_type": source_type,
                "domain": item.get("url", "").replace("https://", "").replace("http://", "").split("/")[0]
            })
        
        return results
    
    def _search_google_cse(self, query: str, max_results: int) -> List[Dict]:
        """Busca usando Google Custom Search JSON API."""
        params = {
            "q": query,
            "key": GOOGLE_CSE_API_KEY,
            "cx": GOOGLE_CSE_CX,
            "num": max_results
        }
        
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for item in data.get("items", [])[:max_results]:
            source_type = self._classify_document(
                item.get("link", ""),
                item.get("title", ""),
                item.get("snippet", "")
            )
            
            results.append({
                "title": item.get("title", ""),
                "href": item.get("link", ""),
                "body": item.get("snippet", ""),
                "auto_type": source_type,
                "domain": item.get("link", "").replace("https://", "").replace("http://", "").split("/")[0]
            })
        
        return results
    
    def download_document(self, url: str, source_type: str, theme: str = "") -> Optional[Document]:
        """
        Descarga un documento (PDF o HTML) y lo guarda localmente.
        """
        try:
            # Verificar si ya existe
            existing = self.db.query(Document).filter(Document.url == url).first()
            if existing:
                return existing
            
            # Determinar directorio según tipo
            save_dir = HEGEMONIC_DIR if source_type == "hegemonic" else SITUATED_DIR
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Descargar contenido
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Generar nombre de archivo
            content_type = response.headers.get("Content-Type", "").lower()
            if "pdf" in content_type or url.lower().endswith(".pdf"):
                ext = ".pdf"
            else:
                ext = ".html"
            
            # Sanitizar título para nombre de archivo
            title = response.headers.get("Content-Disposition", "")
            if "filename=" in title:
                filename = title.split("filename=")[1].strip('"')
            else:
                filename = f"doc_{int(datetime.now().timestamp())}{ext}"
            
            file_path = save_dir / filename
            file_path.write_bytes(response.content)
            
            # Extraer texto para indexación
            content = self._extract_text(file_path)
            
            # Crear registro en BD
            doc = Document(
                title=filename.replace(ext, ""),
                url=url,
                source_type=source_type,
                file_path=str(file_path),
                content=content[:10000],  # Guardar primeros 10k caracteres
                theme=theme,
                date_downloaded=datetime.utcnow(),
                indexed=False
            )
            
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)
            
            return doc
            
        except Exception as e:
            print(f"Error descargando {url}: {e}")
            return None
    
    def _extract_text(self, file_path: Path) -> str:
        """Extrae texto de un archivo (PDF o HTML)."""
        if file_path.suffix.lower() == ".pdf":
            try:
                doc = fitz.open(str(file_path))
                return "\n".join(page.get_text() for page in doc)
            except Exception:
                return ""
        else:
            try:
                from bs4 import BeautifulSoup
                html = file_path.read_text(encoding="utf-8", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                # Eliminar scripts y estilos
                for script in soup(["script", "style", "noscript"]):
                    script.decompose()
                return soup.get_text(separator="\n", strip=True)
            except Exception:
                return file_path.read_text(encoding="utf-8", errors="ignore")
    
    def index_document(self, doc_id: int) -> bool:
        """Indexa un documento en FAISS."""
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            import numpy as np
            import json
            
            doc = self.db.query(Document).get(doc_id)
            if not doc or not doc.file_path or doc.indexed:
                return False
            
            # Extraer texto
            text = self._extract_text(Path(doc.file_path))
            if not text:
                return False
            
            # Generar embeddings
            model = self._get_model()
            embeddings = model.encode([text[:5000]])  # Limitar a 5000 caracteres
            
            # Cargar o crear índice FAISS
            index_path = EMBEDDINGS_DIR / "documents.faiss"
            mapping_path = EMBEDDINGS_DIR / "documents_mapping.json"
            
            if index_path.exists():
                index = faiss.read_index(str(index_path))
                mapping = json.loads(mapping_path.read_text())
            else:
                index = faiss.IndexFlatIP(EMBEDDING_DIM)
                mapping = {"faiss_pos": {}, "sqlite_id": {}}
            
            # Añadir embedding al índice
            next_pos = len(mapping["faiss_pos"])
            index.add(embeddings)
            mapping["faiss_pos"][next_pos] = doc_id
            mapping["sqlite_id"][doc_id] = next_pos
            
            # Guardar índice y mapeo
            faiss.write_index(index, str(index_path))
            mapping_path.write_text(json.dumps(mapping))
            
            # Marcar como indexado
            doc.indexed = True
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error indexando documento {doc_id}: {e}")
            return False
    
    def search_documents(self, query: str, k: int = 5) -> List[Dict]:
        """Busca documentos usando FAISS."""
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            import json
            import numpy as np
            
            model = self._get_model()
            query_embedding = model.encode([query])
            
            index_path = EMBEDDINGS_DIR / "documents.faiss"
            mapping_path = EMBEDDINGS_DIR / "documents_mapping.json"
            
            if not index_path.exists():
                return []
            
            index = faiss.read_index(str(index_path))
            mapping = json.loads(mapping_path.read_text())
            
            # Buscar en FAISS
            D, I = index.search(query_embedding, k)
            
            results = []
            for idx, score in zip(I[0], D[0]):
                doc_id = mapping["faiss_pos"][int(idx)]
                doc = self.db.query(Document).get(doc_id)
                if doc:
                    results.append({
                        "id": doc.id,
                        "title": doc.title,
                        "url": doc.url,
                        "source_type": doc.source_type,
                        "theme": doc.theme,
                        "score": float(score),
                        "file_path": doc.file_path
                    })
            
            return results
            
        except Exception as e:
            print(f"Error buscando documentos: {e}")
            return []
    
    def analyze_document(self, doc_id: int) -> Dict:
        """Analiza un documento (resumen, palabras clave, entidades)."""
        doc = self.db.query(Document).get(doc_id)
        if not doc or not doc.file_path:
            return {}
        
        text = self._extract_text(Path(doc.file_path))
        if not text:
            return {}
        
        return {
            "resumen": self._summarize(text),
            "palabras_clave": self._extract_keywords(text),
            "entidades": self._extract_entities(text)
        }
    
    def _summarize(self, text: str, sentences: int = 5) -> str:
        """Genera un resumen usando LexRank."""
        try:
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            from sumy.summarizers.lex_rank import LexRankSummarizer
            
            parser = PlaintextParser.from_string(text[:10000], Tokenizer("spanish"))
            summarizer = LexRankSummarizer()
            summary = summarizer(parser.document, sentences)
            return " ".join(str(s) for s in summary)
        except Exception:
            return text[:500] + "..."
    
    def _extract_keywords(self, text: str, n: int = 10) -> List[str]:
        """Extrae palabras clave usando TF-IDF."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
            if not sentences:
                return []
            
            vectorizer = TfidfVectorizer(max_features=50, stop_words=["el", "la", "de", "del", "y", "a", "en"])
            X = vectorizer.fit_transform(sentences)
            scores = X.toarray().mean(axis=0)
            terms = vectorizer.get_feature_names_out()
            
            return [t for t, _ in sorted(zip(terms, scores), key=lambda x: -x[1])][:n]
        except Exception:
            return []
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extrae entidades (personas, organizaciones, lugares) usando spaCy."""
        try:
            import spacy
            nlp = spacy.load("es_core_news_md")
            doc = nlp(text[:50000])  # Limitar texto para rendimiento
            
            entities = {"PER": [], "ORG": [], "LOC": [], "GPE": []}
            for ent in doc.ents:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text.strip())
            
            # Eliminar duplicados
            for label in entities:
                entities[label] = list(set(entities[label]))[:10]
            
            return entities
        except Exception:
            return {"PER": [], "ORG": [], "LOC": [], "GPE": []}


# Función para obtener el modelo (singleton)
def _get_model():
    """Carga el modelo de embeddings (singleton)."""
    from sentence_transformers import SentenceTransformer
    from .config import MODELS_DIR, EMBEDDING_MODEL
    
    model_path = MODELS_DIR / EMBEDDING_MODEL
    if model_path.exists():
        return SentenceTransformer(str(model_path))
    else:
        model = SentenceTransformer(EMBEDDING_MODEL)
        model.save(str(model_path))
        return model
