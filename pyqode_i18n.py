'''
Created on 1 de nov. de 2015

@author: martin
'''

_dict = {
    "es": {
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
        "Case": "[TODO] Case",
        "Go to assignments": "[TODO] Go to assignments",
        "Comment/Uncomment": "Comentar/Descomentar",
        "Show documentation": "Ver documentación",
        "Folding": "[TODO] Folding",
        "Encodings": "Codificación",
        "Select word": "Seleccionar palabra",
        "Select extended word": "Seleccionar palabra extendida",
        "Matched select": "[TODO] Matched select",
        "Select line": "Seleccionar linea",
        "Select all": "Seleccionar todo",
        "Search and replace": "Buscar y reemplazar",
        "Find next": "Encontrar siguiente",
        "Find previous": "Encontrar anterior",
        "Convert to lower case ": "Convertir a minusculas",
        "Convert to UPPER CASE ": "Convertir a MAYUSCULAS",
    }
}

def tr(text, lang = "es"):
    if text in _dict[lang].keys():
        return _dict[lang][text]
    else:
        return "*{}".format(text)
