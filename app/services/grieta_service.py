"""
Servicio Grieta para TEKIA.
Análisis cruzado entre corpus hegemónico y situado.
"""
import re
from pathlib import Path
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Document
from ..config import BIAS_VOCAB_DIR


class GrietaService:
    """
    Genera análisis cruzado entre documentos hegemónicos y situados.
    
    Métodos de análisis:
    - Resumen (LexRank)
    - Léxico (TF-IDF)
    - Silencios (términos ausentes)
    - Actores (NER con spaCy)
    - Cronología (extracción de fechas)
    - Divergencia (similaridad coseno)
    - Sesgos epistémicos
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._nlp = None
        self._load_vocab()
    
    def _load_vocab(self):
        """Carga vocabulario de sesgo."""
        heg_file = BIAS_VOCAB_DIR / "hegemonic_terms.txt"
        sit_file = BIAS_VOCAB_DIR / "situated_terms.txt"
        
        self.heg_vocab = set(
            heg_file.read_text(encoding="utf-8").lower().splitlines()
        ) if heg_file.exists() else set()
        self.sit_vocab = set(
            sit_file.read_text(encoding="utf-8").lower().splitlines()
        ) if sit_file.exists() else set()
        
        # Términos por defecto
        if not self.heg_vocab:
            self.heg_vocab = {
                "desarrollo", "progreso", "modernización", "civilización",
                "crecimiento", "inversión", "mercado", "empresa", "gobierno",
                "seguridad", "estabilidad", "orden", "ley", "desarrollo sostenible",
                "competitividad", "productividad", "eficiencia", "globalización"
            }
        if not self.sit_vocab:
            self.sit_vocab = {
                "resistencia", "autonomía", "soberanía", "despojo",
                "lucha", "comunidad", "pueblo", "indígena", "campesino",
                "derechos", "justicia", "liberación", "territorio", "agua",
                "defensa", "organización", "colectivo", "asamblea"
            }
    
    def _nlp_model(self):
        """Carga el modelo spaCy (lazy loading)."""
        if self._nlp is None:
            import spacy
            try:
                self._nlp = spacy.load("es_core_news_md")
            except OSError:
                # Fallback a modelo pequeño si el mediano no está disponible
                self._nlp = spacy.load("es_core_news_sm")
        return self._nlp
    
    def _get_text(self, doc_id: int) -> str:
        """Obtiene el texto completo de un documento."""
        doc = self.db.query(Document).get(doc_id)
        if not doc or not doc.file_path:
            return ""
        
        file_path = Path(doc.file_path)
        if not file_path.exists():
            return ""
        
        if file_path.suffix.lower() == ".pdf":
            try:
                import fitz
                return "\n".join(page.get_text() for page in fitz.open(str(file_path)))
            except Exception:
                return ""
        else:
            try:
                return file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return ""
    
    def generar(self, doc_ids_heg: List[int], doc_ids_sit: List[int]) -> Dict:
        """
        Genera el análisis de la Grieta entre documentos hegemónicos y situados.
        
        Args:
            doc_ids_heg: Lista de IDs de documentos hegemónicos
            doc_ids_sit: Lista de IDs de documentos situados
        
        Returns:
            Dict con todos los análisis
        """
        # Obtener textos
        texts_heg = [t for did in doc_ids_heg if (t := self._get_text(did))]
        texts_sit = [t for did in doc_ids_sit if (t := self._get_text(did))]
        
        # Si no hay documentos de un tipo, devolver análisis vacío
        if not texts_heg and not texts_sit:
            return {"error": "No hay documentos para analizar"}
        
        result = {
            "resumen_heg": "",
            "resumen_sit": "",
            "lexicon": {},
            "silencios": {},
            "actores": [],
            "cronologia": [],
            "divergencia": 0.0,
            "sesgos": {},
            "visualizaciones": {}
        }
        
        # Resúmenes
        if texts_heg:
            result["resumen_heg"] = self._summarize(texts_heg)
        if texts_sit:
            result["resumen_sit"] = self._summarize(texts_sit)
        
        # Léxico (TF-IDF)
        if texts_heg or texts_sit:
            result["lexicon"] = self._lexicon(texts_heg, texts_sit)
        
        # Silencios
        if texts_heg or texts_sit:
            result["silencios"] = self._silencios(texts_heg, texts_sit)
        
        # Actores
        if texts_heg or texts_sit:
            result["actores"] = self._actores(texts_heg, texts_sit)
        
        # Cronología
        if texts_heg or texts_sit:
            result["cronologia"] = self._cronologia(texts_heg, texts_sit)
        
        # Divergencia
        if texts_heg and texts_sit:
            result["divergencia"] = self._divergencia(texts_heg, texts_sit)
        
        # Sesgos epistémicos
        if texts_heg or texts_sit:
            result["sesgos"] = self._detectar_sesgos(texts_heg, texts_sit)
        
        # Visualizaciones (datos para gráficos)
        if texts_heg or texts_sit:
            result["visualizaciones"] = self._generar_visualizaciones(texts_heg, texts_sit)
        
        return result
    
    def _summarize(self, texts: List[str], sentences: int = 5) -> str:
        """Genera un resumen usando LexRank."""
        if not texts:
            return ""
        
        combined = " ".join(t[:20000] for t in texts[:4])
        
        try:
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            from sumy.summarizers.lex_rank import LexRankSummarizer
            
            parser = PlaintextParser.from_string(combined, Tokenizer("spanish"))
            summarizer = LexRankSummarizer()
            summary = summarizer(parser.document, sentences)
            return " ".join(str(s) for s in summary)
        except Exception:
            return combined[:800] + "..."
    
    def _tfidf_top(self, texts: List[str], n: int = 40) -> List[str]:
        """Extrae los términos más importantes usando TF-IDF."""
        if not texts:
            return []
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            vectorizer = TfidfVectorizer(
                max_features=300, 
                min_df=1,
                stop_words=["el", "la", "de", "del", "y", "a", "en", "los", "las", "un", "una"]
            )
            mat = vectorizer.fit_transform(texts)
            scores = mat.toarray().mean(axis=0)
            terms = vectorizer.get_feature_names_out()
            
            return [t for t, _ in sorted(zip(terms, scores), key=lambda x: -x[1]) if len(t) > 3][:n]
        except Exception:
            return []
    
    def _lexicon(self, texts_heg: List[str], texts_sit: List[str]) -> Dict:
        """Análisis léxico: términos exclusivos y compartidos."""
        heg_terms = set(self._tfidf_top(texts_heg, 50))
        sit_terms = set(self._tfidf_top(texts_sit, 50))
        
        return {
            "exclusivo_heg": sorted(heg_terms - sit_terms)[:20],
            "exclusivo_sit": sorted(sit_terms - heg_terms)[:20],
            "compartido": sorted(heg_terms & sit_terms)[:15]
        }
    
    def _silencios(self, texts_heg: List[str], texts_sit: List[str]) -> Dict:
        """Detecta términos del vocabulario de sesgo ausentes en cada corpus."""
        txt_heg = " ".join(texts_heg).lower()
        txt_sit = " ".join(texts_sit).lower()
        
        return {
            "heg_silencia": [
                t for t in sorted(self.sit_vocab) 
                if t.lower() not in txt_heg and len(t) > 3
            ][:15],
            "sit_silencia": [
                t for t in sorted(self.heg_vocab) 
                if t.lower() not in txt_sit and len(t) > 3
            ][:15],
        }
    
    def _actores(self, texts_heg: List[str], texts_sit: List[str]) -> List[Dict]:
        """Extrae actores (entidades) y sus verbos asociados."""
        nlp = self._nlp_model()
        
        def extract_entities_with_verbs(texts: List[str]) -> Dict[str, List[str]]:
            """Extrae entidades y verbos asociados en sus oraciones."""
            entity_verbs = {}
            for text in texts[:2]:  # Limitar a primeros 2 documentos
                doc = nlp(text[:40000])  # Limitar texto
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "PER", "GPE"):
                        # Obtener verbos en la misma oración
                        verbs = [
                            t.lemma_ for t in ent.sent 
                            if t.pos_ == "VERB" and t.text.lower() not in ["ser", "estar", "tener", "hablar"]
                        ]
                        if verbs:
                            entity_verbs.setdefault(ent.text.strip(), []).extend(verbs)
            
            # Eliminar duplicados y limitar
            return {k: list(set(v))[:5] for k, v in list(entity_verbs.items())[:15]}
        
        heg_entities = extract_entities_with_verbs(texts_heg)
        sit_entities = extract_entities_with_verbs(texts_sit)
        
        # Actores compartidos
        shared_entities = set(heg_entities.keys()) & set(sit_entities.keys())
        
        return [
            {
                "actor": actor,
                "heg_verbos": heg_entities.get(actor, []),
                "sit_verbos": sit_entities.get(actor, [])
            }
            for actor in list(shared_entities)[:8]
        ]
    
    def _cronologia(self, texts_heg: List[str], texts_sit: List[str]) -> List[Dict]:
        """Extrae eventos cronológicos (años y contexto)."""
        import dateparser
        
        # Patrones para fechas en español
        date_patterns = [
            r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4}\b',
            r'\b\d{1,2}\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4}\b',
            r'\b\d{4}\b'
        ]
        
        def extract_events(texts: List[str], src: str) -> List[Dict]:
            """Extrae eventos de una lista de textos."""
            results = []
            for text in texts[:2]:  # Limitar a primeros 2 documentos
                for pattern in date_patterns:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        try:
                            date_str = match.group()
                            parsed = dateparser.parse(date_str, languages=["es"])
                            if parsed and 1900 <= parsed.year <= 2030:
                                # Extraer contexto alrededor de la fecha
                                start = max(0, match.start() - 80)
                                end = min(len(text), match.end() + 80)
                                context = text[start:end].replace("\n", " ").strip()[:120]
                                results.append({
                                    "year": parsed.year,
                                    "date": date_str,
                                    "ctx": context,
                                    "src": src
                                })
                        except Exception:
                            continue
            return results
        
        all_events = extract_events(texts_heg, "heg") + extract_events(texts_sit, "sit")
        
        # Agrupar por año
        by_year = {}
        for event in all_events:
            year = event["year"]
            by_year.setdefault(year, {"heg": [], "sit": []})
            by_year[year][event["src"]].append(event["ctx"])
        
        # Ordenar por año y limitar
        return [
            {
                "year": year,
                "heg": by_year[year]["heg"][:2],
                "sit": by_year[year]["sit"][:2]
            }
            for year in sorted(by_year.keys())[-15:]
        ]
    
    def _divergencia(self, texts_heg: List[str], texts_sit: List[str]) -> float:
        """Calcula la divergencia entre corpus usando similaridad coseno."""
        if not texts_heg or not texts_sit:
            return 0.0
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Combinar textos
            text_heg = " ".join(texts_heg)
            text_sit = " ".join(texts_sit)
            
            vectorizer = TfidfVectorizer(max_features=500, stop_words=["el", "la", "de", "del"])
            mat = vectorizer.fit_transform([text_heg, text_sit])
            similarity = cosine_similarity(mat[0:1], mat[1:2])[0][0]
            
            return round(1.0 - float(similarity), 3)
        except Exception:
            return 0.0
    
    def _detectar_sesgos(self, texts_heg: List[str], texts_sit: List[str]) -> Dict:
        """Detecta sesgos epistémicos en los corpus."""
        txt_heg = " ".join(texts_heg).lower()
        txt_sit = " ".join(texts_sit).lower()
        
        # Contar términos de vocabulario
        heg_in_heg = sum(1 for t in self.heg_vocab if t in txt_heg)
        heg_in_sit = sum(1 for t in self.heg_vocab if t in txt_sit)
        sit_in_heg = sum(1 for t in self.sit_vocab if t in txt_heg)
        sit_in_sit = sum(1 for t in self.sit_vocab if t in txt_sit)
        
        # Calcular proporciones
        total_heg_terms = len(self.heg_vocab)
        total_sit_terms = len(self.sit_vocab)
        
        return {
            "heg_en_heg": heg_in_heg / total_heg_terms if total_heg_terms > 0 else 0,
            "heg_en_sit": heg_in_heg / total_heg_terms if total_heg_terms > 0 else 0,
            "sit_en_heg": sit_in_heg / total_sit_terms if total_sit_terms > 0 else 0,
            "sit_en_sit": sit_in_sit / total_sit_terms if total_sit_terms > 0 else 0,
            "dominancia_heg": "hegemónico" if heg_in_heg > sit_in_heg else "situado",
            "dominancia_sit": "hegemónico" if heg_in_sit > sit_in_sit else "situado"
        }
    
    def _generar_visualizaciones(self, texts_heg: List[str], texts_sit: List[str]) -> Dict:
        """Genera datos para visualizaciones (gráficos)."""
        # Datos para gráfico de divergencia
        divergencia = self._divergencia(texts_heg, texts_sit) if texts_heg and texts_sit else 0.0
        
        # Datos para gráfico de léxico
        lexicon = self._lexicon(texts_heg, texts_sit)
        
        # Datos para gráfico de cronología
        cronologia = self._cronologia(texts_heg, texts_sit)
        years = [e["year"] for e in cronologia]
        heg_counts = [len(e["heg"]) for e in cronologia]
        sit_counts = [len(e["sit"]) for e in cronologia]
        
        return {
            "divergencia": {
                "value": divergencia,
                "label": f"Divergencia: {divergencia:.2%}"
            },
            "lexicon": {
                "exclusivo_heg": lexicon.get("exclusivo_heg", []),
                "exclusivo_sit": lexicon.get("exclusivo_sit", []),
                "compartido": lexicon.get("compartido", [])
            },
            "cronologia": {
                "years": years,
                "heg_counts": heg_counts,
                "sit_counts": sit_counts
            },
            "sesgos": self._detectar_sesgos(texts_heg, texts_sit)
        }
