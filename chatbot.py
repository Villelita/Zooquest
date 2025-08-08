import random
import unicodedata
import re
from difflib import SequenceMatcher
from pymongo import MongoClient
from datetime import datetime

# Conexión a MongoDB Atlas (ajusta tu URI)
client = MongoClient("mongodb+srv://jrc4905:1234@ma2025.lxjra0n.mongodb.net/") #Se conecta a la base de datos de MongoDB usando un enlace especial
db = client["zooquest_bot"] #Accede a la base de datos con el nombre zooquest_bot 

faq_collection = db["respuestas"] #Usa una “tabla” dentro de esa base de datos, llamada respuestas (donde están las preguntas y respuestas del bot).
historial_collection = db["historial"] #Usa otra “tabla” llamada historial (donde se guarda lo que los usuarios preguntaron).

def normalizar_texto(texto): #Crea una función para limpiar el texto que escribe el usuario.
    texto = texto.lower() #Convierte todo el texto a letras minúsculas.
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto) #Es un bucle que recorre letra por letra el texto descompuesto. nfd descompone las letras en dos partes, la letra y su acento, en caso de tenerlo.
        if unicodedata.category(c) != 'Mn' #si la letra no es una Mn se conserva, que es la categoria de texto con acentos
    )
    texto = re.sub(r'[^\w\s]', '', texto) #Elimina signos raros, como puntos, comas, símbolos, etc.
    texto = texto.strip() #Elimina espacios al inicio y al final.
    return texto #regresa el texto limpio

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio() #Esta función dice qué tan parecidos son dos textos. El resultado es un número entre 0 (nada parecido) y 1 (idénticos).

def responder_a_usuario(mensaje):
    mensaje_normalizado = normalizar_texto(mensaje) #Limpia el mensaje del usuario.

    # Obtener todas las FAQs
    todas_faq = list(faq_collection.find()) #Busca todas las preguntas y respuestas guardadas en la base de datos.

    # Comprobar si el mensaje es un tema exacto
    temas = [normalizar_texto(faq["tema"]) for faq in todas_faq]
    if mensaje_normalizado in temas:
        # Buscar preguntas del tema
        for faq in todas_faq:
            if normalizar_texto(faq["tema"]) == mensaje_normalizado:
                preguntas = faq["preguntas"]
                sugerencias = "\n".join(f"• {p}" for p in preguntas) # SE TRAE LAS SUGERENCIAS DEL TEMA 
                return f"Esto es lo que puedes preguntarme sobre '{faq['tema']}':\n{sugerencias}"

    # Buscar mejor respuesta por similitud
    mejor_puntaje = 0
    mejor_respuesta = None

    for faq in todas_faq:
        for pregunta in faq["preguntas"]:
            pregunta_normalizada = normalizar_texto(pregunta)
            puntaje = similar(mensaje_normalizado, pregunta_normalizada)
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_respuesta = random.choice(faq["respuestas"]) #Revisa todas las preguntas para ver cuál se parece más a lo que dijo el usuario. Si la encuentra, guarda la mejor respuesta al azar.

    if mejor_puntaje >= 0.6:
        return mejor_respuesta
    else:
        return "Lo siento, no tengo una respuesta para eso todavía 🐾. ¡Prueba preguntarme otra cosa!"

def guardar_en_historial(mensaje):
    historial_collection.insert_one({
        "mensaje": mensaje,
        "fecha": datetime.now()
    }) #guarda en el hisrtorial con fecha 

def obtener_historial(limit=10):
    historial = list(historial_collection.find().sort("fecha", -1).limit(limit))
    return [
        {"mensaje": h["mensaje"], "fecha": h["fecha"].strftime("%Y-%m-%d %H:%M")}
        for h in historial
    ] #trae los ultimos 10 mensajes enviados al chatbot con su fecha y mensaje humano 

def borrar_historial():
    resultado = historial_collection.delete_many({})
    return resultado.deleted_count #borra del historial xd
