# notas de compatibilidad

los mensajes de datos adjuntos tienen un comportamiento diferente. si se envia un mensaje con los adjuntos, salen en 2 mensajes separados, uno de texto, otro de archivos adjuntos

revisar soporte para multiples media en un solo mensaje, revisado, en whatsapp la media multiple se trata como mensajes individuales, cada uno con su propio comentario opcional, messenger manda todos los archivos como un solo mensaje y el comentario se trata como un primer mensaje diferente, y en otra solicitud(POST)

los tipo media de messenger no tienen

    mime_type: str
    sha256: str
    media_id: str
    
revisar si default o no obligatorios y su impacto en el flujo

consideraciones para tipo sticker

    "attachments": [
    {
        "payload": {
            "sticker_id": 380422049561830,
            "url": "https://scontent.xx.fbcdn.net/v/t39.1997-6/70940315_380422062895162_8658590632069038080_n.png?stp=dst-png_s100x100&_nc_cat=1&ccb=1-7&_nc_sid=23dd7b&_nc_ohc=_Aq90NKobpoQ7kNvgE9uHnV&_nc_oc=AdggVwCFVWt6KPLDOPmZLSbZmXPSdNCN6yHUV4xUhxHLEZUnDujDuGtigXyOLxkKloxm7C25WS6ng2jH95IiLAla&_nc_ad=z-m&_nc_cid=0&_nc_zt=26&_nc_ht=scontent.xx&_nc_gid=AB6QsVOrbX8ppXulp-CKy-t&oh=00_AYA_BZkaXpdS3jFIQ3bjTe1nIqdDCOTf4a6bCEpP0pPOHA&oe=67C20D80"
        },
        "type": "image"
    }]
