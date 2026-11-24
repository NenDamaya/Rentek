import re
from pathlib import Path
from typing import Dict, List, Optional, Any


FRONT_MATTER_RE = re.compile(r"^---\s*$", re.MULTILINE)
PRECIO_RE = re.compile(r"\*\*Precio de renta:\*\*\s*(.+)$", re.MULTILINE)
NOMBRE_RE = re.compile(r"\*\*Nombre común:\*\*\s*(.+)$", re.MULTILINE)
MARCAS_RE = re.compile(r"\*\*Marcas:\*\*\s*(.+)$", re.MULTILINE)
MODELOS_RE = re.compile(r"\*\*Modelos típicos:\*\*\s*(.+)$", re.MULTILINE)

FIELD_HEADING_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)
MACHINE_HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
CATEGORY_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _strip_markdown_bold(text: str) -> str:
    return text.replace("**", "")


def _parse_bullet_list(lines: List[str]) -> List[str]:
    items = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:])
        elif re.match(r"^\d+\.\s", stripped):
            items.append(re.sub(r"^\d+\.\s+", "", stripped))
        else:
            items.append(stripped)
    return items


def _extract_field_dict(text: str, field_label: str) -> Dict[str, str]:
    pattern = re.compile(
        rf"### {re.escape(field_label)}\n(.*?)(?=\n###\s|\n##\s|\n#\s|\n---|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return {}
    content = match.group(1).strip()
    result = {}
    for line in content.split("\n"):
        line = line.strip()
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.*)", line)
        if m:
            key = _strip_markdown_bold(m.group(1)).strip()
            value = m.group(2).strip()
            result[key] = value
    return result


def _extract_field_text(text: str, field_label: str) -> str:
    pattern = re.compile(
        rf"### {re.escape(field_label)}\n(.*?)(?=\n###\s|\n##\s|\n#\s|\n---|\Z)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip()


def _extract_field_lines(text: str, field_label: str) -> List[str]:
    raw = _extract_field_text(text, field_label)
    if not raw:
        return []
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    return lines


def _extract_field_items(text: str, field_label: str) -> List[str]:
    lines = _extract_field_lines(text, field_label)
    return _parse_bullet_list(lines)


def _extract_sinonimos(text: str, field_label: str) -> List[str]:
    raw = _extract_field_text(text, field_label)
    if not raw:
        return []
    parts = re.split(r"[,_;]", raw)
    return [p.strip().replace("_", "") for p in parts if p.strip().replace("_", "")]


def _extract_info_general(text: str) -> Dict[str, str]:
    return _extract_field_dict(text, "Información general")


def _extract_especificaciones(text: str) -> Dict[str, str]:
    return _extract_field_dict(text, "Especificaciones técnicas")


def _extract_info_general_simple(text: str, field_label: str) -> Dict[str, str]:
    raw = _extract_field_text(text, field_label)
    if not raw:
        return {}
    result = {}
    for line in raw.split("\n"):
        line = line.strip()
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.*)", line)
        if m:
            key = _strip_markdown_bold(m.group(1)).strip()
            value = m.group(2).strip()
            result[key] = value
        m2 = re.match(r"^- (.+?):\s*(.*)", line)
        if m2 and not line.startswith("- **"):
            result[m2.group(1).strip()] = m2.group(2).strip()
    return result


MACHINE_FIELDS = [
    "sinonimos",
    "perfil_cliente",
    "info_general",
    "especificaciones",
    "recomendado",
    "no_recomendado",
    "casos_uso",
    "preguntas_frecuentes",
    "reglas_negocio",
]

FIELD_MAP = {
    "sinonimos": ("Sinónimos y variantes de lenguaje", "sinonimos"),
    "perfil_cliente": ("Perfil del cliente ideal", "items"),
    "info_general": ("Información general", "dict"),
    "especificaciones": ("Especificaciones técnicas", "dict"),
    "recomendado": ("Recomendado para ✅", "items"),
    "no_recomendado": ("No recomendado para ❌", "items"),
    "casos_uso": ("Casos de uso", "items"),
    "preguntas_frecuentes": ("Preguntas frecuentes", "qa"),
    "reglas_negocio": ("Reglas de negocio / Criterios de recomendación", "items"),
}


def _parse_qa(lines: List[str]) -> List[Dict[str, str]]:
    qa_list = []
    for line in lines:
        m = re.match(r"^- \*\*(.+?)\?\*\*\s*(.*)", line)
        if m:
            qa_list.append({"pregunta": m.group(1) + "?", "respuesta": m.group(2).strip()})
    return qa_list


class Catalogo:
    def __init__(self, filepath: str = None):
        if filepath is None:
            base = Path(__file__).resolve().parent.parent
            filepath = str(base / "data" / "documentos" / "Maquinarias.md")
        self.filepath = filepath
        self._categorias: Dict[str, Any] = {}
        self._proyectos: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        text = Path(self.filepath).read_text(encoding="utf-8")

        text = FRONT_MATTER_RE.split(text, 2)
        if len(text) > 2:
            text = text[2]
        else:
            text = text[-1]

        sections = re.split(r"\n(?=#\s)", text)
        for section in sections:
            section = section.strip()
            if not section:
                continue

            cat_match = re.match(r"^#\s+(.+)$", section, re.MULTILINE)
            if not cat_match:
                continue
            cat_name = cat_match.group(1).strip()

            if cat_name == "Proyectos y Combinaciones Frecuentes":
                self._parse_proyectos(section)
            else:
                self._parse_categoria(cat_name, section)

    def _parse_categoria(self, cat_name: str, section: str):
        machines = {}
        machine_blocks = re.split(r"\n(?=##\s)", section)
        for block in machine_blocks:
            block = block.strip()
            mach_match = re.match(r"^##\s+(.+)$", block, re.MULTILINE)
            if not mach_match:
                continue
            mach_name = mach_match.group(1).strip()

            machine = self._parse_maquina(block)
            machines[mach_name] = machine

        if machines:
            self._categorias[cat_name] = {
                "nombre": cat_name,
                "maquinas": machines,
            }

    def _parse_maquina(self, block: str) -> Dict[str, Any]:
        machine = {}
        for key, (field_name, field_type) in FIELD_MAP.items():
            if field_type == "sinonimos":
                value = _extract_sinonimos(block, field_name)
            elif field_type == "dict":
                value = _extract_info_general_simple(block, field_name)
            elif field_type == "items":
                value = _extract_field_items(block, field_name)
            elif field_type == "qa":
                lines = _extract_field_lines(block, field_name)
                value = _parse_qa(lines)
            else:
                value = _extract_field_items(block, field_name)
            if value:
                machine[key] = value

        precio_match = PRECIO_RE.search(block)
        if precio_match:
            machine["precio_renta"] = precio_match.group(1).strip()

        nombre_match = NOMBRE_RE.search(block)
        if nombre_match:
            machine["nombre_comun"] = nombre_match.group(1).strip()

        marcas_match = MARCAS_RE.search(block)
        if marcas_match:
            machine["marcas"] = marcas_match.group(1).strip()

        modelos_match = MODELOS_RE.search(block)
        if modelos_match:
            machine["modelos_tipicos"] = modelos_match.group(1).strip()

        return machine

    def _parse_proyectos(self, section: str):
        project_blocks = re.split(r"\n(?=##\s)", section)
        for block in project_blocks:
            block = block.strip()
            proj_match = re.match(r"^##\s+(.+)$", block, re.MULTILINE)
            if not proj_match:
                continue
            proj_name = proj_match.group(1).strip()

            maquinarias = []
            in_consideraciones = False
            consideraciones_lines = []
            for line in block.split("\n"):
                line = line.strip()
                if line.startswith("### Consideraciones técnicas"):
                    in_consideraciones = True
                    continue
                if line.startswith("### ") and "Consideraciones" not in line:
                    in_consideraciones = False
                if in_consideraciones:
                    consideraciones_lines.append(line)
                    continue
                if line.startswith("- ") and not in_consideraciones:
                    maquinarias.append(line[2:])

            consideraciones = "\n".join(consideraciones_lines).strip()

            self._proyectos.append({
                "nombre": proj_name,
                "maquinarias": maquinarias,
                "consideraciones": consideraciones if consideraciones else "",
            })

    def get_categorias(self) -> Dict[str, Any]:
        return dict(self._categorias)

    def get_categoria(self, nombre: str) -> Optional[Dict[str, Any]]:
        for key, cat in self._categorias.items():
            if key.lower() == nombre.lower():
                return cat
        return None

    def get_maquina(self, nombre: str) -> Optional[Dict[str, Any]]:
        nombre_lower = nombre.lower()
        for cat in self._categorias.values():
            for key, machine in cat["maquinas"].items():
                if nombre_lower in key.lower():
                    return {"categoria": cat["nombre"], "nombre": key, **machine}
                comunes = machine.get("nombre_comun", "").lower()
                if nombre_lower in comunes:
                    return {"categoria": cat["nombre"], "nombre": key, **machine}
                sinonimos = [s.lower() for s in machine.get("sinonimos", [])]
                if nombre_lower in sinonimos:
                    return {"categoria": cat["nombre"], "nombre": key, **machine}
        return None

    def buscar(self, termino: str) -> List[Dict[str, Any]]:
        termino_lower = termino.lower()
        results = []
        for cat_name, cat in self._categorias.items():
            for mach_name, machine in cat["maquinas"].items():
                score = 0
                if termino_lower in mach_name.lower():
                    score += 3
                comunes = machine.get("nombre_comun", "").lower()
                if termino_lower in comunes:
                    score += 2
                sinonimos = [s.lower() for s in machine.get("sinonimos", [])]
                if any(termino_lower in s for s in sinonimos):
                    score += 2
                info_text = str(machine.get("info_general", {}))
                if termino_lower in info_text.lower():
                    score += 1
                recomendado = " ".join(machine.get("recomendado", []))
                if termino_lower in recomendado.lower():
                    score += 1

                if score > 0:
                    results.append({
                        "score": score,
                        "categoria": cat_name,
                        "nombre": mach_name,
                        "nombre_comun": machine.get("nombre_comun", ""),
                        "precio_renta": machine.get("precio_renta", ""),
                        "info_general": machine.get("info_general", {}),
                        "especificaciones": machine.get("especificaciones", {}),
                    })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_proyectos(self) -> List[Dict[str, Any]]:
        return list(self._proyectos)

    def get_proyecto(self, nombre: str) -> Optional[Dict[str, Any]]:
        for proj in self._proyectos:
            if nombre.lower() in proj["nombre"].lower():
                return proj
        return None

    def resumen_categorias(self) -> List[Dict[str, Any]]:
        resumen = []
        for cat_name, cat in self._categorias.items():
            machines_list = []
            for mach_name, machine in cat["maquinas"].items():
                machines_list.append({
                    "nombre": mach_name,
                    "nombre_comun": machine.get("nombre_comun", ""),
                    "precio_renta": machine.get("precio_renta", ""),
                    "marcas": machine.get("marcas", ""),
                    "modelos_tipicos": machine.get("modelos_tipicos", ""),
                })
            resumen.append({
                "nombre": cat_name,
                "total_maquinas": len(machines_list),
                "maquinas": machines_list,
            })
        return resumen
