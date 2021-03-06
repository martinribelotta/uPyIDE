# -*- coding: UTF-8 -*-

_dict = {
    "es": {
        "Edu CIAA MicroPython": "Edu CIAA MicroPython",
        "Open": "Abrir",
        "Save": "Guardar",
        "New": "Nuevo",
        "Run": "Ejecutar",
        "About": "Acerca de...",
        "Help": "Ayuda",
        "Terminal": "Terminal",
        "To Editor": "Al Editor",
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
        "Serial Port:": "Puerto Serial:",
        "NewFile.py (%d)": "Nuevo.py (%d)",
        "Remote Name": "Nombre Remoto",
        "Select Serial Port": "Seleccionar Puerto Serie"
    },
    "zh_TW": {
        "Edu CIAA MicroPython": "Edu CIAA MicroPython",
        "Open": "開啟",
        "Save": "儲存",
        "New": "新檔案",
        "Run": "執行",
        "About": "關於...",
        "Help": "幫助",
        "Terminal": "終端機",
        "To Editor": "到編輯器",
        "Outline": "大綱",
        "Snipplets": "片段",
        "Download": "下載",
        "Undo": "復原",
        "Redo": "重做",
        "Cut": "剪下",
        "Copy": "複製",
        "Paste": "貼上",
        "Duplicate line": "複製此行",
        "Delete": "刪除",
        "Indent": "縮排",
        "Un-indent": "取消縮排",
        "Go to line": "Go to line",
        "Search": "尋找",
        "Select": "選取",
        "Case": "Case",
        "Go to assignments": "Go to assignments",
        "Comment/Uncomment": "註解/取消註解",
        "Show documentation": "顯示文件",
        "Folding": "折疊",
        "Encodings": "編碼",
        "Select word": "選取字",
        "Select extended word": "選取延伸字",
        "Matched select": "[TODO] 匹配選取",
        "Select line": "選取行",
        "Select all": "選取全部",
        "Search and replace": "尋找和取代",
        "Find next": "找下一個",
        "Find previous": "找前一個",
        "Convert to lower case": "轉為小寫",
        "Convert to UPPER CASE": "轉為大寫",
        "Question": "問題",
        "Document was modify": "文件已經被修改",
        "Save changes?": "儲存修改?",
        "Save File": "儲存檔案",
        "Open File": "開啟檔案",
        "Python files (*.py);;All files (*)": "Python 檔案(*.py);;"
                                              "所有檔案 (*)",
        "Serial Port:": "序列埠:",
        "NewFile.py (%d)": "新檔案.py (%d)",
        "Remote Name": "遠端名稱",
        "Select Serial Port": "選取序列埠",
        "Device files": "裝置的檔案",
        "Refresh": "重新整理",
        "Device": "裝置",
        "Download to Device": "上傳到裝置"
    }
}


def tr(text, lang="es"):
    if lang in _dict and text in _dict[lang].keys():
        return _dict[lang][text]
    else:
        return "*{}".format(text)
