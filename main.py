from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI(
    title="Social Media Video Downloader API",
    description="API que extrae formatos disponibles de video y audio utilizando yt-dlp"
)

# Permitir CORS para poder consumir la API desde cualquier aplicación o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/info")
def get_video_info(url: str = Query(..., description="URL del video de la red social")):
    # Configuración de yt-dlp para extraer datos sin descargar el archivo real
    ydl_opts = {
        'extract_flat': False,
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraer metadatos completos de la URL de forma segura
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise HTTPException(status_code=404, detail="No se pudo obtener información de la URL.")
            
            formatos_video = []
            formatos_audio = []
            
            # Recorrer todos los formatos disponibles que entrega la plataforma
            for f in info.get('formats', []):
                # Filtrar y formatear las opciones de Video
                if f.get('vcodec') != 'none':
                    formatos_video.append({
                        "format_id": f.get("format_id"),
                        "resolution": f.get("resolution") or f"{f.get('width')}x{f.get('height')}",
                        "ext": f.get("ext"),
                        "fps": f.get("fps"),
                        "filesize_mb": round(f.get("filesize", 0) / (1024 * 1024), 2) if f.get("filesize") else "Desconocido",
                        "url": f.get("url"), # Enlace directo de descarga provisto por la red social
                        "note": f.get("format_note")
                    })
                
                # Filtrar y formatear las opciones de Audio
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    formatos_audio.append({
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "abr_kbps": f.get("abr"), # Bitrate de audio (calidad)
                        "filesize_mb": round(f.get("filesize", 0) / (1024 * 1024), 2) if f.get("filesize") else "Desconocido",
                        "url": f.get("url"),
                        "note": f.get("format_note")
                    })
            
            # Retornar el JSON estructurado con la metadata limpia
            return {
                "title": info.get("title"),
                "duration_seconds": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader"),
                "platform": info.get("extractor_key"),
                "video_options": formatos_video,
                "audio_options": formatos_audio
            }
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar la URL: {str(e)}")
