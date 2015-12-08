# -*- coding: UTF-8 -*-

_dict = {
    "es": {
        "Edu CIAA MicroPython": "Edu CIAA MicroPython",
        "Open": "Abrir",
        "Save": "Guardar",
        "New": "Nuevo",
        "Run": "Ejecutar",
        "Terminal": "Terminal",
        "Outline": "Simbolos",
        "Snipplets": "Trozos de codigo",
        "Download": "Grabar",
        "Undo": "Deshacer",
        "Redo": "Rehacer",
        "Cut": "Cortar",
        "Copy": "Copiar",
        "Paste": "Pegar",
        "Duplicate line": "Duplicar Linea",
        "Delete": "Borrar",
        "Indent": "Identar",
        "Un-indent": "Desidentar",
        "Go to line": "Ir a la linea",
        "Search": "Buscar",
        "Select": "Seleccionar",
        "Case": "Capitalización",
        "Go to assignments": "Ir a...",
        "Comment/Uncomment": "Comentar/Descomentar",
        "Show documentation": "Ver documentación",
        "Folding": "Plegar codigo",
        "Encodings": "Codificación",
        "Select word": "Seleccionar palabra",
        "Select extended word": "Seleccionar palabra extendida",
        "Matched select": "[TODO] Matched select",
        "Select line": "Seleccionar linea",
        "Select all": "Seleccionar todo",
        "Search and replace": "Buscar y reemplazar",
        "Find next": "Encontrar siguiente",
        "Find previous": "Encontrar anterior",
        "Convert to lower case": "Convertir a minusculas",
        "Convert to UPPER CASE": "Convertir a MAYUSCULAS",
        "Question": "Pregunta",
        "Document was modify": "El documento se ha modificado",
        "Save changes?": "¿Guardar los cambios?",
        "Save File": "Guardar Archivo",
        "Open File": "Abrir Archivo",
        "Python files (*.py);;All files (*)": "Archivos Python (*.py);;"
                                              "Todos los archivos (*)",
        "Serial Port:": "Puerto Serial:"
    }
}


def tr(text, lang="es"):
    if lang in _dict and text in _dict[lang].keys():
        return _dict[lang][text]
    else:
        return "*{}".format(text)
