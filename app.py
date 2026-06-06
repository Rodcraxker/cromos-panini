from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io, os
import mediapipe as mp 
import cv2
import numpy as np
from rembg import remove

app = Flask(__name__)

# Función auxiliar para cargar fuentes
def obtener_fuente(nombre, tamano):
    ruta_local = os.path.join(os.path.dirname(__file__), 'Montserrat', 'static', nombre)
    if not os.path.exists(ruta_local):
        ruta_alt = os.path.join(os.path.dirname(__file__), 'Montserrat', nombre)
        if os.path.exists(ruta_alt):
            return ImageFont.truetype(ruta_alt, tamano)
        return ImageFont.load_default()
    return ImageFont.truetype(ruta_local, tamano)

# Función para centrar texto en un ancho determinado
def alinear_texto(draw, texto, font, y_pos, x_inicio):
    # Simplemente dibuja el texto en x_inicio, sin sumar ningún cálculo de centrado
    draw.text((x_inicio, y_pos), texto, fill="white", font=font)

@app.route('/')
def index():
    return render_template('index.html')

def recortar_rostro(foto_data):

    # 1. Abrir la imagen original
    img_original = Image.open(io.BytesIO(foto_data)).convert("RGBA")
    
    if img_original.width > 800:
        img_original.thumbnail((800, 800), Image.Resampling.LANCZOS)
    
    # 3. Eliminar el fondo
    # Convertimos de nuevo a bytes para rembg
    buffer = io.BytesIO()
    img_original.save(buffer, format="PNG")
    output_bytes = remove(buffer.getvalue())
    
    # 4. Abrir la silueta resultante
    img_silueta = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    
    # 5. Ajustar al tamaño del hueco del cromo (520x580)
    target_size = (520, 580)
    img_silueta.thumbnail(target_size, Image.Resampling.LANCZOS)
    
    # 6. Crear lienzo transparente y centrar
    final_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
    paste_x = (target_size[0] - img_silueta.width) // 2
    paste_y = (target_size[1] - img_silueta.height) // 2
    
    final_img.paste(img_silueta, (paste_x, paste_y), img_silueta)
    
    return final_img

@app.route('/eliminar_fondo', methods=['POST'])
def eliminar_fondo():
    if 'foto' not in request.files:
        return "No se encontró archivo", 400
    
    file = request.files['foto']
    
    # 1. Leemos el archivo en bytes
    img_data = file.read()
    
    # 2. Procesamos con rembg
    img_sin_fondo = remove(img_data)
    
    # 3. Creamos un buffer para enviarlo de vuelta
    output = io.BytesIO(img_sin_fondo)
    output.seek(0)
    
    return send_file(output, mimetype='image/png')

def generar_sticker(foto_data, datos):
    # 1. Abrimos la imagen
    base = Image.open(io.BytesIO(foto_data)).convert("RGBA")
    draw = ImageDraw.Draw(base)
    
    # 2. Obtenemos dimensiones dinámicas
    w, h = base.size
    
    # 3. Definimos fuentes escaladas según la altura de la imagen
    font_nombre = obtener_fuente("Montserrat-Black.ttf", int(h * 0.04))
    font_apellido = obtener_fuente("Montserrat-Black.ttf", int(h * 0.045))
    font_info = obtener_fuente("Montserrat-Black.ttf", int(h * 0.025))
    font_inst = obtener_fuente("Montserrat-Black.ttf", int(h * 0.03))
    
    # 4. Procesamos datos
    nombre_completo = datos['nombre'].upper()
    partes = nombre_completo.split()
    nombre = partes[0]
    apellido = " ".join(partes[1:]) if len(partes) > 1 else ""
    info_str = f"{datos['fecha']} | {datos['estatura']}m | {datos['peso']}kg"
    
    # 5. Coordenadas relativas (Ajusta los porcentajes si el texto queda muy arriba o abajo)
    y_textos = int(h * 0.82) # Altura base donde empieza el nombre


    y_info = int(h * 0.88)

    # PUCETEC DS (UIO) un poco más abajo
    y_inst = int(h * 0.93)
    
    # 6. Lógica de centrado para Nombre y Apellido (combinados)
    espacio_entre = int(w * 0.01)
    w_nombre = draw.textlength(nombre, font=font_nombre)
    w_apellido = draw.textlength(apellido, font=font_apellido)
    ancho_total = w_nombre + espacio_entre + w_apellido
    x_inicial = (w - ancho_total) / 2
    
    # Dibujar Nombre y Apellido
    draw.text((x_inicial, y_textos), nombre, fill="white", font=font_nombre)
    draw.text((x_inicial + w_nombre + espacio_entre, y_textos), apellido, fill="white", font=font_apellido)
    
    # 7. Dibujar Info adicional e Institución usando tu función centrar_texto
    # Asegúrate de que centrar_texto acepte el ancho total (w)
    centrar_texto(draw, info_str, font_info, y_info, 0, w)
    centrar_texto(draw, "PUCETEC DS (UIO)", font_inst, y_inst, 0, w)
    
    # 8. Guardar y retornar
    output = io.BytesIO()
    base.save(output, format="PNG")
    return output.getvalue()

@app.route('/procesar_cromo', methods=['POST'])
def procesar_cromo():
    datos = {
        'nombre': request.form.get('nombre', 'JUGADOR'),
        'fecha': request.form.get('fecha', '2000-01-01'),
        'estatura': request.form.get('estatura', '1.70'),
        'peso': request.form.get('peso', '70')
    }
    file = request.files['foto']
    
    img = Image.open(io.BytesIO(file.read())).convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size 
    
    # 1. POSICIONES Y MÁRGENES
    y_nombre = int(h * 0.800) 
    y_info = int(h * 0.850)   
    y_inst = int(h * 0.895)  
    
    margen_izquierdo = int(w * 0.25)

    # 2. Fuentes
    font_nombre = obtener_fuente("Montserrat-Black.ttf", int(h * 0.038))
    font_info = obtener_fuente("Montserrat-Black.ttf", int(h * 0.022))
    
    nombre_completo = datos['nombre'].upper()
    partes = nombre_completo.split()
    nombre = partes[0]
    apellido = " ".join(partes[1:]) if len(partes) > 1 else ""

    
    # 5. Centrado dentro de la franja
    espacio_entre = int(w * 0.01)

    draw.text((margen_izquierdo, y_nombre), nombre, fill="white", font=font_nombre)
    
    # Calcular dónde empieza el apellido (Nombre + espacio)
    w_n = draw.textlength(nombre, font=font_nombre)
    draw.text((margen_izquierdo + w_n + espacio_entre, y_nombre), apellido, fill="white", font=font_nombre)
    
    
    info_str = f"{datos['fecha']} | {datos['estatura']}m | {datos['peso']}kg"

    alinear_texto(draw, info_str, font_info, y_info, margen_izquierdo)
    alinear_texto(draw, "PUCETEC DS (UIO)", font_info, y_inst, margen_izquierdo)
    
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)