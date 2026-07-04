# tekia_github
Sistema sofisticado de organización de datos de primer nivel. 

TEKIA es un sistema local soberano de investigación: descarga fuentes hegemónicas y situadas, las indexa, permite análisis (resumen, keywords, NER, sesgo epistémico), y las vincula a un cuaderno de notas propio exportable. Sin nube, sin LLM, sin telemetría.

Descarga fuentes hegemónicas y situadas, las indexa, permite análisis (resumen, keywords, NER, sesgo epistémico), y las vincula a un cuaderno de notas propio exportable. Sin nube, sin LLM, sin telemetría. 

🔹 Objetivo Principal
Sistema local que:
1. Descargue documentos** de medios **hegemónicos y situados (páginas web o PDFs).
2. Organice los documentos en carpetas locales (`hegemonic/`, `situated/`).
3. Permita analizar los documentos (sin LLM, solo Python) para extraer:
- Entrega lo más representativo de hegemónico y lo más representativo de situado
   - Resúmenes.
   - Palabras clave.
   - Patrones (ej: fechas, nombres, sesgos).
   - Entidades (personas, organizaciones, lugares).
4.Incluya un sistema de notas (como Upnote o Notion, pero **100% local**) donde:
   - Puedas **escribir análisis** vinculados a los documentos.
   - Las notas estén **organizadas por temas y etiquetas**.
   - Puedas **buscar** en las notas (por texto, etiquetas, temas).
5.Todo debe ser soberano:
   - Sin nube: Todo se guarda en tu máquina.
   - Sin telemetría: Ningún dato sale de tu equipo.
   - Sin dependencias externas: Solo librerías de Python locales.


Revisa la arquitectura que tengo construida hasta ahora y hazle las correcciones necesarias para que cumpla su objetivo.
NOTA:
Si hay mejoras que no tenga contempladas propónmelas, lo que buscamos es llevar el sistema al nivel más sofisticado siendo soberano y veloz. Potente. Es para un ciéntifico de datos, arquitecto RAG, investigador autónomo y del CLACSO.


