# app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from chatbot import responder_a_usuario, guardar_en_historial, obtener_historial, borrar_historial, historial_collection
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'  

print("\nConnecting to MongoDB Atlas...")
def verificar_conexion():
    print("hols")
    try:
        client = MongoClient(
            "mongodb+srv://Ariel_Nieto:dbUSERpassword@ma2025.86lehds.mongodb.net/",
            serverSelectionTimeoutMS=5000
        )
        client.server_info()
        print("[SUCCESS] Connected to MongoDB Atlas")
        return client['zooquest']  # Devuelve la colección completa
    except ConnectionFailure:
        print("[ERROR] Connection failed")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected problem: {str(e)}")
        return None
    
db=verificar_conexion()
animls=db['animals']
users=db['users']
cromos=db['cromos']

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Para redirigir cuando se necesite login
# Configuración de la carpeta de subida de imágenes
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Usuario(UserMixin):
    def __init__(self, usuario_data):
        self.id = str(usuario_data['_id'])
        self.nombre = usuario_data['name']
        self.correo = usuario_data['email']
        self.descripcion = usuario_data['description']
        self.cromos = usuario_data.get('cromos', [])
        self.password_hash = usuario_data['password']
        self.fecha_nacimiento = usuario_data['birth_date']
        self.fecha_registro = usuario_data.get('fecha_registro', datetime.utcnow())
    
    @staticmethod
    def get_by_id(user_id):
        usuario_data = users.find_one({'_id': ObjectId(user_id)})
        if not usuario_data:
            return None
        return Usuario(usuario_data)
    
    @staticmethod
    def get_by_email(correo):
        usuario_data = users.find_one({'email': correo})
        if not usuario_data:
            return None
        return Usuario(usuario_data)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.get_by_id(user_id)


# RUTAS HTML
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/habitats")
def habitats():
    return render_template("habitats.html")

@app.route("/juegos")
def juegos():
    return render_template("juegos.html")

@app.route("/cromos")
@login_required
def ver_cromos():
    user_id = current_user.get_id()
    user = users.find_one({'_id': ObjectId(user_id)})

    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('login'))

    color_classes = {
        'selva': 'green-card',
        'sabana': 'orange-card',
        'oceano': 'blue-card',
        'ártico': 'grey-card',
        'artico': 'grey-card',
        'desierto': 'yellow-card'
    }

    cromos_usuario = []
    for cromo_id in user.get('cromos', []):
        cromo = cromos.find_one({'_id': cromo_id})
        if cromo:
            habitat = cromo.get('habitat', '').lower()
            cromo['color'] = color_classes.get(habitat, 'default-card')
            cromos_usuario.append(cromo)

    return render_template("cromos.html", cromos=cromos_usuario)

@app.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    user_id = current_user.get_id()
    
    # Obtener datos del formulario
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    cumpleanos = request.form.get('cumpleanos')
    
    # Preparar los datos a actualizar
    update_data = {
        'name': nombre,
        'description': descripcion
    }
    
    if cumpleanos:
        try:
            update_data['birth_date'] = datetime.strptime(cumpleanos, '%Y-%m-%d')
        except ValueError:
            flash('Formato de fecha inválido', 'error')
            return redirect(url_for('usuario'))
    
    # Manejar la imagen subida
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            update_data['profile_image'] = filename
    
    # Actualizar en la base de datos
    users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': update_data}
    )
    
    flash('Perfil actualizado correctamente', 'success')
    return redirect(url_for('usuario'))

@app.route("/usuario")
@login_required
def usuario():
    user_id = current_user.get_id()
    user = users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('login'))
    
    # Formatear fechas
    birth_date = user.get('birth_date')
    formatted_birthday = birth_date.strftime('%d de %B') if birth_date else "No especificado"
    
    # Calcular tiempo en el sitio
    registration_date = user.get('fecha_registro', datetime.utcnow())
    hours_on_site = int((datetime.utcnow() - registration_date).total_seconds() / 3600)
    
    # Obtener imagen de perfil (si existe)
    profile_image = user.get('profile_image', 'Blueprint.png')
    
    return render_template("usuario.html", 
                         name=user.get('name', 'Usuario'),
                         description=user.get('description', 'No hay descripción'),
                         birthday=formatted_birthday,
                         birth_date=birth_date,  # Para el datepicker
                         playtime=f"{hours_on_site} hrs",
                         profile_image=profile_image)

@app.route("/asistente")
def asistente():
    return render_template("asistente.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('usuario'))  # Redirige a la página de perfil si ya está logueado

    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        
        usuario = Usuario.get_by_email(correo)
        
        if not usuario or not usuario.verify_password(password):
            flash('Correo o contraseña incorrectos', 'error')
            return redirect(url_for('login'))
        
        login_user(usuario)
        flash('Has iniciado sesión correctamente', 'success')
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('usuario'))  # Redirige a perfil o a la página solicitada
    
    return render_template('login.html')  # Asegúrate de que coincida con tu template

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        fecha_nacimiento_str = request.form['fecha_nacimiento']
        
        # Validaciones básicas
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('register'))
        
        if users.find_one({'correo': correo}):
            flash('Este correo ya está registrado', 'error')
            return redirect(url_for('register'))
        
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d')
        except ValueError:
            flash('Formato de fecha incorrecto', 'error')
            return redirect(url_for('register'))
        
        # Crear nuevo usuario
        nuevo_usuario = {
            'name': nombre,
            'email': correo,
            'description': request.form.get('descripcion', 'No hay descripción'),  # Campo opcional
            'cromos': [],  # Inicializar con una lista vacía
            'password': generate_password_hash(password, method='pbkdf2:sha256'),
            'birth_date': fecha_nacimiento,
            'fecha_registro': datetime.utcnow()
        }
        
        # Insertar en MongoDB
        usuario_id = users.insert_one(nuevo_usuario).inserted_id
        
        # Crear objeto Usuario para Flask-Login
        usuario = Usuario.get_by_id(usuario_id)
        
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))  # Redirigir a login (a implementar después)
    return render_template("register.html")

@app.route("/oceano")
def oceano():
    try:
        # Buscar animales cuyo hábitat incluya "desert"
        animales_oceano = list(animls.find({"habitat": {"$regex": "ocean", "$options": "i"}}))
        
        # Procesar datos para la plantilla
        animales_procesados = []
        for animal in animales_oceano:
            animal_data = {
                'id': str(animal['_id']),
                'nombre': animal.get('name', 'Sin nombre'),
                'imagen': animal.get('image', '/static/img/default-animal.jpg'),
                'audio': animal.get('sound', '/static/audio/default-audio.mp3'),
                'descripcion': animal.get('description', 'Descripción no disponible')
            }
            animales_procesados.append(animal_data)
        
        return render_template("oceano.html", animales=animales_procesados)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return render_template("oceano.html",animales=[]) 
    
@app.route("/animalsOcean/<animal_id>")
def animalsOcean(animal_id):
    try:
        animal = animls.find_one({"_id": ObjectId(animal_id)})
        if not animal:
            return redirect(url_for('oceano'))
            
        return render_template("animalsOcean.html", animal={
            'nombre': animal.get('name', 'Camello'),  # Valor por defecto específico
            'imagen': animal.get('image', '/static/img/camello.jpg'),
            'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
            'descripcion': animal.get('description', 'Descripción del camello')
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('oceano'))

@app.route("/artico")
def artico():
    try:
        # Buscar animales cuyo hábitat incluya "desert"
        animales_artico = list(animls.find({"habitat": {"$regex": "arctic", "$options": "i"}}))
        
        # Procesar datos para la plantilla
        animales_procesados = []
        for animal in animales_artico:
            animal_data = {
                'id': str(animal['_id']),
                'nombre': animal.get('name', 'Sin nombre'),
                'imagen': animal.get('image', '/static/img/default-animal.jpg'),
                'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
                'descripcion': animal.get('description', 'Descripción no disponible')
            }
            animales_procesados.append(animal_data)
        
        return render_template("artico.html", animales=animales_procesados)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return render_template("artico.html",animales=[]) 
    
@app.route("/animalsArctic/<animal_id>")
def animalsArctic(animal_id):
    try:
        animal = animls.find_one({"_id": ObjectId(animal_id)})
        if not animal:
            return redirect(url_for('artico'))
            
        return render_template("animalsArctic.html", animal={
            'nombre': animal.get('name', 'Camello'),  # Valor por defecto específico
            'imagen': animal.get('image', '/static/img/camello.jpg'),
            'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
            'descripcion': animal.get('description', 'Descripción del camello')
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('artico'))

@app.route("/selva")
def selva():
    try:
        # Buscar animales cuyo hábitat incluya "desert"
        animales_selva = list(animls.find({"habitat": {"$regex": "jungle", "$options": "i"}}))
        
        # Procesar datos para la plantilla
        animales_procesados = []
        for animal in animales_selva:
            animal_data = {
                'id': str(animal['_id']),
                'nombre': animal.get('name', 'Sin nombre'),
                'imagen': animal.get('image', '/static/img/default-animal.jpg'),
                'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
                'descripcion': animal.get('description', 'Descripción no disponible')
            }
            animales_procesados.append(animal_data)
        
        return render_template("selva.html", animales=animales_procesados)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return render_template("selva.html",animales=[]) 
    
@app.route("/animalsJungle/<animal_id>")
def animalsJungle(animal_id):
    try:
        animal = animls.find_one({"_id": ObjectId(animal_id)})
        if not animal:
            return redirect(url_for('selva'))
            
        return render_template("animalsJungle.html", animal={
            'nombre': animal.get('name', 'Camello'),  # Valor por defecto específico
            'imagen': animal.get('image', '/static/img/camello.jpg'),
            'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
            'descripcion': animal.get('description', 'Descripción del camello')
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('selva'))

@app.route("/sabana")
def sabana():
    try:
        # Buscar animales cuyo hábitat incluya "desert"
        animales_sabana = list(animls.find({"habitat": {"$regex": "savanna", "$options": "i"}}))
        
        # Procesar datos para la plantilla
        animales_procesados = []
        for animal in animales_sabana:
            animal_data = {
                'id': str(animal['_id']),
                'nombre': animal.get('name', 'Sin nombre'),
                'imagen': animal.get('image', '/static/img/default-animal.jpg'),
                'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
                'descripcion': animal.get('description', 'Descripción no disponible')
            }
            animales_procesados.append(animal_data)
        
        return render_template("sabana.html", animales=animales_procesados)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return render_template("sabana.html",animales=[]) 
    
@app.route("/animalsSavanna/<animal_id>")
def animalsSavanna(animal_id):
    try:
        animal = animls.find_one({"_id": ObjectId(animal_id)})
        if not animal:
            return redirect(url_for('sabana'))
            
        return render_template("animalsSavanna.html", animal={
            'nombre': animal.get('name', 'Camello'),  # Valor por defecto específico
            'imagen': animal.get('image', '/static/img/camello.jpg'),
            'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
            'descripcion': animal.get('description', 'Descripción del camello')
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('sabana'))

@app.route("/desierto")
def desierto():
    try:
        # Buscar animales cuyo hábitat incluya "desert"
        animales_desierto = list(animls.find({"habitat": {"$regex": "desert", "$options": "i"}}))
        
        # Procesar datos para la plantilla
        animales_procesados = []
        for animal in animales_desierto:
            animal_data = {
                'id': str(animal['_id']),
                'nombre': animal.get('name', 'Sin nombre'),
                'imagen': animal.get('image', '/static/img/default-animal.jpg'),
                'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
                'descripcion': animal.get('description', 'Descripción no disponible')
            }
            animales_procesados.append(animal_data)
        
        return render_template("desierto.html", animales=animales_procesados)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return render_template("desierto.html",animales=[])  # Retorna una lista vacía en caso de error

@app.route("/animalsDesert/<animal_id>")
def animalsDesert(animal_id):
    try:
        animal = animls.find_one({"_id": ObjectId(animal_id)})
        if not animal:
            return redirect(url_for('desierto'))
            
        return render_template("animalsDesert.html", animal={
            'nombre': animal.get('name', 'Camello'),  # Valor por defecto específico
            'imagen': animal.get('image', '/static/img/camello.jpg'),
            'audio': animal.get('sound', '/static/audio/chinese-gong.mp3'),
            'descripcion': animal.get('description', 'Descripción del camello')
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return redirect(url_for('desierto'))

# RUTA DE CHATBOT
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    guardar_en_historial(user_message)
    respuesta = responder_a_usuario(user_message)

    return jsonify({"response": respuesta})



# RUTA DE HISTORIAL
@app.route("/historial")
def historial():
    return jsonify(obtener_historial())

@app.route("/borrar_historial", methods=["DELETE"])
def ruta_borrar_historial():
    cantidad = borrar_historial()
    return jsonify({"mensaje": f"Historial borrado correctamente. Registros eliminados: {cantidad}"}), 200

if __name__ == "__main__":
    app.run(debug=True)
