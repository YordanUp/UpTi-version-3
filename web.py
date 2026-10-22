from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import uuid
import re
from urllib.parse import urlparse
from sqlalchemy import or_, func
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
app.secret_key = os.environ.get('SECRET_KEY', 'cambia_esto_en_produccion')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'uptisoporte@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = ('UPTI Soporte', os.environ.get('MAIL_USERNAME', 'uptisoporte@gmail.com'))

mail = Mail(app)

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:UpTi_db16@localhost:5432/upti_db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

PROFILE_PICS_FOLDER = os.path.join(basedir, 'static', 'perfiles')
if not os.path.exists(PROFILE_PICS_FOLDER):
    os.makedirs(PROFILE_PICS_FOLDER)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'txt', 'xlsx', 'pptx'}
ALLOWED_PROFILE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# ─────────────────────────────────────────────
# GROQ IA
# ─────────────────────────────────────────────
from groq import Groq

groq_client = None

def init_gemini():
    global groq_client
    api_key = os.environ.get('GEMINI_API_KEY', '')
    print(f"KEY GROQ: {api_key[:20]}...")
    if api_key:
        groq_client = Groq(api_key=api_key)
        print("✓ IA inicializada (Groq)")

# ─────────────────────────────────────────────
# MODELOS
# ─────────────────────────────────────────────
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(256), nullable=False)
    imagen_perfil = db.Column(db.String(255), nullable=False, default='default.png')
    cuatrimestre_id = db.Column(db.Integer, db.ForeignKey('cuatrimestre.id'), nullable=True)
    grupo = db.Column(db.String(10), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)

class Cuatrimestre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False, unique=True)

class Materia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    cuatrimestre_id = db.Column(db.Integer, db.ForeignKey('cuatrimestre.id'), nullable=False)

class Tema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    youtube_url = db.Column(db.String(255), nullable=True)
    etiquetas = db.Column(db.String(200), default='')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.id'), nullable=False)

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    youtube_url = db.Column(db.String(255), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    tema_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

class Archivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.Text)
    tema_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    es_fijo = db.Column(db.Boolean, default=False)
    es_enlace = db.Column(db.Boolean, default=False)

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    expiracion = db.Column(db.DateTime, nullable=False)

class Reaccion(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tipo_objeto = db.Column(db.String(20), nullable=False)
    objeto_id   = db.Column(db.Integer, nullable=False)
    emoji       = db.Column(db.String(10), nullable=False)
    fecha       = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('usuario_id', 'tipo_objeto', 'objeto_id', 'emoji', name='uq_reaccion'),)

# Relaciones
Usuario.temas = db.relationship('Tema', backref='autor', lazy=True)
Usuario.comentarios = db.relationship('Comentario', backref='autor', lazy=True)
Usuario.archivos = db.relationship('Archivo', backref='autor', lazy=True)
Usuario.cuatrimestre = db.relationship('Cuatrimestre', backref='usuarios')
Cuatrimestre.materias = db.relationship('Materia', backref='cuatrimestre', lazy=True)
Materia.temas = db.relationship('Tema', backref='materia', lazy=True)
Tema.comentarios = db.relationship('Comentario', backref='tema', lazy=True, cascade='all, delete-orphan')
Tema.archivos = db.relationship('Archivo', backref='tema', lazy=True, cascade='all, delete-orphan')
PasswordResetToken.usuario = db.relationship('Usuario')

# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_profile_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PROFILE_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def extract_youtube_id(url):
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

def extract_youtube_url(text):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    match = re.search(youtube_regex, text)
    if match:
        return f"https://youtube.com/watch?v={match.group(6)}"
    return None

@app.template_filter('extract_youtube_id')
def extract_youtube_id_filter(url):
    return extract_youtube_id(url)

def enviar_bienvenida(email, nombre_usuario):
    msg = Message('Bienvenido a UPTI', recipients=[email])
    msg.body = f'''Hola {nombre_usuario},

Gracias por registrarte en UPTI. ¡Esperamos que disfrutes la experiencia!

Saludos,
Equipo UPTI'''
    mail.send(msg)

# ─────────────────────────────────────────────
# RUTAS AUTENTICACIÓN
# ─────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_input = request.form.get('usuario')
        contraseña_input = request.form.get('contraseña')
        user = Usuario.query.filter(
            or_(Usuario.correo == usuario_input, Usuario.nombre_usuario == usuario_input)
        ).first()
        if user and check_password_hash(user.contraseña, contraseña_input):
            session['user_id'] = user.id
            session['user_correo'] = user.correo
            session['user_nombre'] = user.nombre_usuario
            session['user_imagen'] = user.imagen_perfil
            return redirect(url_for('inicio'))
        else:
            flash("Usuario o contraseña incorrectos", "danger")
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        correo = request.form['correo']
        nombre_usuario = request.form['nombre_usuario']
        contraseña = request.form['contraseña']
        imagen = request.files.get('imagen_perfil')

        if Usuario.query.filter_by(correo=correo).first():
            flash("Correo ya registrado", "danger")
            return redirect(url_for('registro'))
        if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
            flash("Nombre de usuario ya existe", "danger")
            return redirect(url_for('registro'))

        if imagen and allowed_profile_file(imagen.filename):
            filename = secure_filename(imagen.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            imagen.save(os.path.join(PROFILE_PICS_FOLDER, unique_name))
        else:
            unique_name = 'default.png'

        hash_pass = generate_password_hash(contraseña)
        nuevo_usuario = Usuario(correo=correo, nombre_usuario=nombre_usuario,
                                contraseña=hash_pass, imagen_perfil=unique_name)
        db.session.add(nuevo_usuario)
        db.session.commit()

        try:
            enviar_bienvenida(correo, nombre_usuario)
        except Exception as e:
            print(f"Error enviando correo de bienvenida: {e}")

        flash("Registro exitoso. Por favor inicia sesión.", "success")
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/recuperar_contraseña', methods=['GET', 'POST'])
def recuperar_contraseña():
    if request.method == 'POST':
        correo = request.form.get('correo')
        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario:
            token = uuid.uuid4().hex
            expiracion = datetime.utcnow() + timedelta(hours=1)
            PasswordResetToken.query.filter_by(usuario_id=usuario.id).delete()
            db.session.add(PasswordResetToken(token=token, usuario_id=usuario.id, expiracion=expiracion))
            db.session.commit()
            reset_link = url_for('resetear_contraseña', token=token, _external=True)
            msg = Message('Recuperación de contraseña UPTI', recipients=[correo])
            msg.body = f'Hola {usuario.nombre_usuario},\n\nPara restablecer tu contraseña haz clic aquí (válido 1 hora):\n\n{reset_link}\n\nSi no solicitaste esto, ignora este correo.\n\nEquipo UPTI'
            mail.send(msg)
            flash("Correo enviado con instrucciones para restablecer tu contraseña.", "success")
            return redirect(url_for('login'))
        else:
            flash("No existe un usuario registrado con ese correo.", "danger")
    return render_template('recuperar_contraseña.html')

@app.route('/resetear_contraseña/<token>', methods=['GET', 'POST'])
def resetear_contraseña(token):
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_token or reset_token.expiracion < datetime.utcnow():
        flash("El enlace ha expirado o no es válido.", "danger")
        return redirect(url_for('login'))
    if request.method == 'POST':
        nueva_contraseña = request.form.get('contraseña')
        reset_token.usuario.contraseña = generate_password_hash(nueva_contraseña)
        db.session.delete(reset_token)
        db.session.commit()
        flash("Contraseña actualizada correctamente. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for('login'))
    return render_template('resetear_contraseña.html', token=token)

# ─────────────────────────────────────────────
# RUTAS PRINCIPALES
# ─────────────────────────────────────────────
@app.route('/')
@login_required
def inicio():
    import json
    cuatrimestres = Cuatrimestre.query.all()
    usuario = Usuario.query.get(session['user_id'])
    cuatrimestres_json = json.dumps([{'id': c.id, 'nombre': c.nombre} for c in cuatrimestres])
    return render_template('cuatrimestres.html', cuatrimestres=cuatrimestres,
                           usuario=usuario, cuatrimestres_json=cuatrimestres_json)

@app.route('/cuatrimestre/<int:cuatrimestre_id>')
@login_required
def ver_cuatrimestre(cuatrimestre_id):
    cuatrimestre = Cuatrimestre.query.get_or_404(cuatrimestre_id)
    usuario = Usuario.query.get(session['user_id'])
    return render_template('materias.html', cuatrimestre=cuatrimestre,
                           usuario=usuario, materias=cuatrimestre.materias)

@app.route('/materia/<int:materia_id>')
@login_required
def ver_materia(materia_id):
    materia = Materia.query.get_or_404(materia_id)
    usuario = Usuario.query.get(session['user_id'])
    return render_template('ver_materia.html', materia=materia, usuario=usuario)

@app.route('/materia/<int:materia_id>/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_tema(materia_id):
    usuario = Usuario.query.get(session['user_id'])
    materia = Materia.query.get_or_404(materia_id)
    if request.method == 'POST':
        titulo      = request.form['titulo']
        contenido   = request.form['contenido']
        youtube_url = extract_youtube_url(contenido)
        etiquetas = request.form.get('etiquetas', '').strip()
        nuevo = Tema(titulo=titulo, contenido=contenido, youtube_url=youtube_url,
                     etiquetas=etiquetas, autor_id=usuario.id, materia_id=materia_id,
                     fecha_creacion=datetime.utcnow())
        db.session.add(nuevo)
        db.session.commit()
        es_enlace = request.form.get('es_enlace', '0') == '1'
        if es_enlace:
            enlace_url  = request.form.get('enlace_url', '').strip()
            descripcion = request.form.get('descripcion_enlace', '').strip()
            if enlace_url:
                try:
                    parsed = urlparse(enlace_url)
                    if not all([parsed.scheme, parsed.netloc]):
                        raise ValueError("URL inválida")
                    db.session.add(Archivo(nombre_archivo=f"Enlace: {parsed.netloc}",
                        ruta=enlace_url, descripcion=descripcion,
                        tema_id=nuevo.id, autor_id=usuario.id,
                        fecha_subida=datetime.utcnow(), es_enlace=True))
                    db.session.commit()
                except ValueError:
                    flash("URL del enlace no válida (debe iniciar con http:// o https://)", "warning")
        else:
            archivo     = request.files.get('archivo')
            descripcion = request.form.get('descripcion_archivo', '').strip()
            if archivo and archivo.filename and allowed_file(archivo.filename):
                filename       = secure_filename(archivo.filename)
                filename_unico = f"{uuid.uuid4().hex}_{filename}"
                archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_unico))
                db.session.add(Archivo(nombre_archivo=filename, ruta=filename_unico,
                    descripcion=descripcion, tema_id=nuevo.id,
                    autor_id=usuario.id, fecha_subida=datetime.utcnow(), es_enlace=False))
                db.session.commit()
        flash("Tema creado exitosamente", "success")
        return redirect(url_for('ver_materia', materia_id=materia_id))
    return render_template('nuevo_tema.html', usuario=usuario, materia_id=materia_id, materia=materia)

@app.route('/tema/<int:tema_id>', methods=['GET', 'POST'])
@login_required
def ver_tema(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    usuario = Usuario.query.get(session['user_id'])
    if request.method == 'POST':
        contenido = request.form['contenido']
        youtube_url = extract_youtube_url(contenido)
        db.session.add(Comentario(contenido=contenido, youtube_url=youtube_url,
                                  tema_id=tema.id, autor_id=session['user_id'],
                                  fecha_creacion=datetime.utcnow()))
        db.session.commit()
        flash("Comentario agregado", "success")
        return redirect(url_for('ver_tema', tema_id=tema.id))
    archivos = Archivo.query.filter_by(tema_id=tema.id).all()
    mis_reacciones = Reaccion.query.filter_by(usuario_id=session['user_id']).all()
    mis_reacciones_set = {(r.tipo_objeto, r.objeto_id, r.emoji) for r in mis_reacciones}
    ids_archivos = [a.id for a in archivos]
    ids_comentarios = [c.id for c in tema.comentarios]
    filtros = [db.and_(Reaccion.tipo_objeto == 'tema', Reaccion.objeto_id == tema_id)]
    if ids_archivos:
        filtros.append(db.and_(Reaccion.tipo_objeto == 'archivo', Reaccion.objeto_id.in_(ids_archivos)))
    if ids_comentarios:
        filtros.append(db.and_(Reaccion.tipo_objeto == 'comentario', Reaccion.objeto_id.in_(ids_comentarios)))
    conteos_raw = db.session.query(
        Reaccion.tipo_objeto, Reaccion.objeto_id, Reaccion.emoji,
        func.count(Reaccion.id).label('total')
    ).filter(db.or_(*filtros)).group_by(
        Reaccion.tipo_objeto, Reaccion.objeto_id, Reaccion.emoji
    ).all()
    conteos = {(tipo, obj_id, emoji): total for tipo, obj_id, emoji, total in conteos_raw}
    return render_template('tema.html', tema=tema, archivos=archivos, usuario=usuario,
                           mis_reacciones_set=mis_reacciones_set, conteos=conteos)

@app.route('/eliminar_comentario/<int:id>', methods=['POST'])
@login_required
def eliminar_comentario(id):
    comentario = Comentario.query.get_or_404(id)
    if comentario.autor_id != session['user_id']:
        flash("No tienes permiso para eliminar este comentario", "danger")
        return redirect(url_for('ver_tema', tema_id=comentario.tema_id))
    tema_id = comentario.tema_id
    db.session.delete(comentario)
    db.session.commit()
    flash("Comentario eliminado", "success")
    return redirect(url_for('ver_tema', tema_id=tema_id))

@app.route('/tema/<int:tema_id>/subir_archivo', methods=['GET', 'POST'])
@login_required
def subir_archivo(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    usuario = Usuario.query.get(session['user_id'])
    if request.method == 'POST':
        content_type = request.form.get('contentType')
        descripcion  = request.form.get('descripcion', '')
        if content_type == 'file':
            if 'archivo' not in request.files:
                flash("No hay archivo seleccionado", "danger")
                return redirect(url_for('subir_archivo', tema_id=tema_id))
            file = request.files['archivo']
            if file.filename == '':
                flash("No se seleccionó archivo", "danger")
                return redirect(url_for('subir_archivo', tema_id=tema_id))
            if file and allowed_file(file.filename):
                filename       = secure_filename(file.filename)
                filename_unico = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_unico))
                db.session.add(Archivo(nombre_archivo=filename, ruta=filename_unico,
                                       descripcion=descripcion, tema_id=tema.id,
                                       autor_id=session['user_id'], fecha_subida=datetime.utcnow(),
                                       es_enlace=False))
                db.session.commit()
                flash("Archivo subido exitosamente", "success")
                return redirect(url_for('ver_tema', tema_id=tema.id))
            else:
                flash("Tipo de archivo no permitido", "danger")
                return redirect(url_for('subir_archivo', tema_id=tema_id))
        elif content_type == 'link':
            link_url = request.form.get('linkUrl', '').strip()
            if not link_url:
                flash("Por favor, introduce un enlace válido", "danger")
                return redirect(url_for('subir_archivo', tema_id=tema_id))
            try:
                parsed_url = urlparse(link_url)
                if not all([parsed_url.scheme, parsed_url.netloc]):
                    raise ValueError("URL inválida")
                db.session.add(Archivo(nombre_archivo=f"Enlace: {parsed_url.netloc}",
                                       ruta=link_url, descripcion=descripcion,
                                       tema_id=tema.id, autor_id=session['user_id'],
                                       fecha_subida=datetime.utcnow(), es_enlace=True))
                db.session.commit()
                flash("Enlace compartido exitosamente", "success")
                return redirect(url_for('ver_tema', tema_id=tema.id))
            except ValueError:
                flash("Por favor, introduce una URL válida (debe comenzar con http:// o https://)", "danger")
                return redirect(url_for('subir_archivo', tema_id=tema_id))
    return render_template('subir_archivo.html', tema=tema, usuario=usuario)

@app.route('/descargar_archivo/<int:archivo_id>')
@login_required
def descargar_archivo(archivo_id):
    archivo = Archivo.query.get_or_404(archivo_id)
    if archivo.es_enlace:
        return redirect(archivo.ruta)
    return send_from_directory(app.config['UPLOAD_FOLDER'], archivo.ruta,
                               as_attachment=True, download_name=archivo.nombre_archivo)

@app.route('/eliminar_archivo/<int:archivo_id>', methods=['POST'])
@login_required
def eliminar_archivo(archivo_id):
    archivo = Archivo.query.get_or_404(archivo_id)
    if archivo.autor_id != session['user_id'] and session['user_id'] != 1:
        flash("No tienes permiso para eliminar este archivo", "danger")
        return redirect(url_for('ver_tema', tema_id=archivo.tema_id))
    if not archivo.es_enlace:
        ruta_fisica = os.path.join(app.config['UPLOAD_FOLDER'], archivo.ruta)
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)
    db.session.delete(archivo)
    db.session.commit()
    flash("Archivo eliminado", "success")
    return redirect(url_for('ver_tema', tema_id=archivo.tema_id))

@app.route('/editar_descripcion/<int:archivo_id>', methods=['POST'])
@login_required
def editar_descripcion(archivo_id):
    archivo = Archivo.query.get_or_404(archivo_id)
    if archivo.autor_id != session['user_id']:
        flash("No tienes permiso para editar este archivo", "danger")
        return redirect(url_for('ver_tema', tema_id=archivo.tema_id))
    archivo.descripcion = request.form.get('nueva_descripcion', '').strip()
    db.session.commit()
    flash("Descripción actualizada", "success")
    return redirect(url_for('ver_tema', tema_id=archivo.tema_id))

@app.route('/ver_archivo/<filename>')
@login_required
def ver_archivo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    usuario = Usuario.query.get(session['user_id'])
    cuatrimestres = Cuatrimestre.query.all()
    if request.method == 'POST':
        nuevo_nombre      = request.form['nombre_usuario'].strip()
        imagen            = request.files.get('imagen_perfil')
        nuevo_cuatrimestre_id = request.form.get('cuatrimestre_id')
        nuevo_grupo       = request.form.get('grupo', '').strip()
        nueva_descripcion = request.form.get('descripcion', '').strip()
        if not nuevo_nombre:
            flash("El nombre de usuario no puede estar vacío.", "danger")
            return redirect(url_for('editar_perfil'))
        if Usuario.query.filter(Usuario.nombre_usuario == nuevo_nombre, Usuario.id != usuario.id).first():
            flash("El nombre de usuario ya está en uso por otro usuario.", "danger")
            return redirect(url_for('editar_perfil'))
        usuario.nombre_usuario = nuevo_nombre
        usuario.grupo          = nuevo_grupo
        usuario.descripcion    = nueva_descripcion
        if nuevo_cuatrimestre_id:
            try:
                cid = int(nuevo_cuatrimestre_id)
                usuario.cuatrimestre_id = cid if Cuatrimestre.query.get(cid) else None
            except:
                usuario.cuatrimestre_id = None
        else:
            usuario.cuatrimestre_id = None
        if imagen and allowed_profile_file(imagen.filename):
            filename    = secure_filename(imagen.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            imagen.save(os.path.join(PROFILE_PICS_FOLDER, unique_name))
            if usuario.imagen_perfil != 'default.png':
                ruta_antigua = os.path.join(PROFILE_PICS_FOLDER, usuario.imagen_perfil)
                if os.path.exists(ruta_antigua):
                    os.remove(ruta_antigua)
            usuario.imagen_perfil = unique_name
        db.session.commit()
        session['user_nombre'] = usuario.nombre_usuario
        session['user_imagen'] = usuario.imagen_perfil
        flash("Perfil actualizado correctamente.", "success")
        return redirect(url_for('inicio'))
    return render_template('editar_perfil.html', usuario=usuario, cuatrimestres=cuatrimestres)

@app.route('/perfil/<int:usuario_id>')
@login_required
def ver_perfil(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    return render_template('perfil.html', usuario=usuario)

@app.route('/perfil_modal/<int:usuario_id>')
@login_required
def perfil_modal(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    return jsonify({
        'nombre_usuario': usuario.nombre_usuario,
        'correo':         usuario.correo,
        'imagen_perfil':  usuario.imagen_perfil,
        'cuatrimestre':   usuario.cuatrimestre.nombre if usuario.cuatrimestre else None,
        'grupo':          usuario.grupo if usuario.grupo and usuario.grupo.strip() else None,
        'descripcion':    usuario.descripcion if usuario.descripcion and usuario.descripcion.strip() else None
    })

@app.route('/eliminar_tema/<int:tema_id>', methods=['POST'])
@login_required
def eliminar_tema(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    if tema.autor_id != session['user_id']:
        flash("No tienes permiso para eliminar este tema", "danger")
        return redirect(url_for('ver_materia', materia_id=tema.materia_id))
    for archivo in tema.archivos:
        if not archivo.es_enlace:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], archivo.ruta))
            except:
                pass
        db.session.delete(archivo)
    for comentario in tema.comentarios:
        db.session.delete(comentario)
    materia_id = tema.materia_id
    db.session.delete(tema)
    db.session.commit()
    flash('Tema eliminado correctamente', 'success')
    return redirect(url_for('ver_materia', materia_id=materia_id))

@app.route('/editar_tema/<int:tema_id>', methods=['GET', 'POST'])
@login_required
def editar_tema(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    if tema.autor_id != session['user_id']:
        flash("No tienes permiso para editar este tema", "danger")
        return redirect(url_for('ver_tema', tema_id=tema.id))
    if request.method == 'POST':
        tema.titulo      = request.form['titulo']
        tema.contenido   = request.form['contenido']
        tema.youtube_url = extract_youtube_url(request.form['contenido'])
        tema.etiquetas   = request.form.get('etiquetas', '').strip()
        db.session.commit()
        flash("Tema actualizado correctamente", "success")
        return redirect(url_for('ver_tema', tema_id=tema.id))
    usuario = Usuario.query.get(session['user_id'])
    return render_template('editar_tema.html', tema=tema, usuario=usuario)

@app.route('/buscar')
@login_required
def buscar():
    query    = request.args.get('q', '').strip()
    usuario  = Usuario.query.get(session['user_id'])
    temas = archivos = materias = usuarios = []
    if query:
        q = f'%{query}%'
        temas    = Tema.query.filter(or_(Tema.titulo.ilike(q), Tema.contenido.ilike(q))).order_by(Tema.fecha_creacion.desc()).limit(20).all()
        archivos = Archivo.query.filter(or_(Archivo.nombre_archivo.ilike(q), Archivo.descripcion.ilike(q))).order_by(Archivo.fecha_subida.desc()).limit(20).all()
        materias = Materia.query.filter(Materia.nombre.ilike(q)).limit(10).all()
        usuarios = Usuario.query.filter(or_(Usuario.nombre_usuario.ilike(q), Usuario.correo.ilike(q))).limit(10).all()
    return render_template('buscar.html', query=query, temas=temas, archivos=archivos,
                           materias=materias, usuarios=usuarios, usuario=usuario)

@app.route('/reaccionar', methods=['POST'])
@login_required
def reaccionar():
    EMOJIS_VALIDOS = ['👍','❤️','🔥','🧠','🎯','😕','👎','❌']
    tipo   = request.form.get('tipo_objeto')
    obj_id = request.form.get('objeto_id', type=int)
    emoji  = request.form.get('emoji')
    if tipo not in ['tema', 'archivo', 'comentario'] or emoji not in EMOJIS_VALIDOS:
        return jsonify({'error': 'Inválido'}), 400
    existing = Reaccion.query.filter_by(usuario_id=session['user_id'], tipo_objeto=tipo, objeto_id=obj_id).first()
    if existing:
        if existing.emoji == emoji:
            db.session.delete(existing)
            db.session.commit()
            activo = False
        else:
            existing.emoji = emoji
            db.session.commit()
            activo = True
    else:
        db.session.add(Reaccion(usuario_id=session['user_id'], tipo_objeto=tipo, objeto_id=obj_id, emoji=emoji))
        db.session.commit()
        activo = True
    count = Reaccion.query.filter_by(tipo_objeto=tipo, objeto_id=obj_id, emoji=emoji).count()
    return jsonify({'activo': activo, 'count': count, 'emoji': emoji})

@app.route('/reac_conteos')
@login_required
def reac_conteos():
    tipo   = request.args.get('tipo')
    obj_id = request.args.get('id', type=int)
    LABELS = {'👍':'Me gusta','❤️':'Me encanta','🔥':'Útil','🧠':'Aprendí','🎯':'Al punto','😕':'Confuso','👎':'No ayuda','❌':'Incorrecto'}
    rows = db.session.query(Reaccion.emoji, func.count(Reaccion.id)).filter_by(tipo_objeto=tipo, objeto_id=obj_id).group_by(Reaccion.emoji).all()
    mias = {r.emoji for r in Reaccion.query.filter_by(usuario_id=session['user_id'], tipo_objeto=tipo, objeto_id=obj_id).all()}
    result = [{'emoji': e, 'count': c, 'mia': e in mias, 'label': LABELS.get(e,'')} for e, c in rows if c > 0]
    return jsonify(result)

# ─────────────────────────────────────────────
# RUTAS IA
# ─────────────────────────────────────────────

@app.route('/ia/chat', methods=['POST'])
@login_required
def ia_chat():
    if not groq_client:
        return jsonify({'error': 'IA no configurada'}), 503
    try:
        data = request.get_json(force=True, silent=True) or {}
        mensaje = data.get('mensaje', '').strip()
        if not mensaje:
            return jsonify({'error': 'Mensaje vacío'}), 400
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres un asistente académico de UPTI (Universidad Politécnica de Tlaxcala Bilingüe). Ayudas a estudiantes con dudas sobre sus materias. Responde siempre en español, de forma clara y concisa."},
                {"role": "user", "content": mensaje}
            ],
            max_tokens=1024
        )
        return jsonify({'respuesta': completion.choices[0].message.content})
    except Exception as e:
        print(f"ERROR IA CHAT: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/ia/resumir_tema/<int:tema_id>', methods=['POST'])
@login_required
def ia_resumir_tema(tema_id):
    if not groq_client:
        return jsonify({'error': 'IA no configurada'}), 503
    tema = Tema.query.get_or_404(tema_id)
    archivos = Archivo.query.filter_by(tema_id=tema_id, es_enlace=False).all()
    contexto = f"Tema: {tema.titulo}\nMateria: {tema.materia.nombre}\nContenido: {tema.contenido}\nArchivos: {', '.join([a.nombre_archivo for a in archivos]) if archivos else 'Ninguno'}"
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres un asistente académico. Responde en español."},
                {"role": "user", "content": f"Analiza este tema académico y proporciona: 1. Resumen (2-3 oraciones) 2. Puntos clave (3-5 puntos) 3. Conceptos importantes\n\n{contexto}"}
            ],
            max_tokens=1024
        )
        return jsonify({'resumen': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ia/sugerencias/<int:materia_id>')
@login_required
def ia_sugerencias(materia_id):
    if not groq_client:
        return jsonify({'error': 'IA no configurada'}), 503
    materia = Materia.query.get_or_404(materia_id)
    temas_existentes = [t.titulo for t in materia.temas[:10]]
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Responde SOLO con un array JSON de 5 strings, sin texto adicional."},
                {"role": "user", "content": f'Sugiere 5 temas de estudio para la materia "{materia.nombre}". Temas existentes: {", ".join(temas_existentes) if temas_existentes else "Ninguno"}. Formato: ["Tema 1", "Tema 2", "Tema 3", "Tema 4", "Tema 5"]'}
            ],
            max_tokens=256
        )
        import json
        texto = re.sub(r'```json|```', '', completion.choices[0].message.content).strip()
        sugerencias = json.loads(texto)
        return jsonify({'sugerencias': sugerencias[:5]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ia/quiz/<int:tema_id>', methods=['POST'])
@login_required
def ia_quiz(tema_id):
    """
    Genera un quizz mixto basado en el contenido del tema.
    Body JSON: { "num_preguntas": 5 }
    Retorna: { "preguntas": [ { "tipo", "pregunta", "opciones"?, "respuesta", "explicacion" } ] }
    """
    if not groq_client:
        return jsonify({'error': 'IA no configurada'}), 503

    tema = Tema.query.get_or_404(tema_id)
    data = request.get_json(force=True, silent=True) or {}
    num  = max(3, min(10, int(data.get('num_preguntas', 5))))

    num_multiple = num // 2
    num_abierta  = num - num_multiple

    contexto = f"Materia: {tema.materia.nombre}\nTema: {tema.titulo}\nContenido:\n{tema.contenido[:3000]}"

    prompt = f"""Eres un profesor universitario. Basándote ÚNICAMENTE en el siguiente contenido académico, crea exactamente {num} preguntas de repaso en español.

{contexto}

Genera:
- {num_multiple} preguntas de opción múltiple (4 opciones, solo una correcta)
- {num_abierta} preguntas de respuesta abierta

Responde ÚNICAMENTE con un array JSON válido, sin texto adicional, sin markdown, sin backticks.
Formato exacto:
[
  {{
    "tipo": "multiple",
    "pregunta": "¿Pregunta aquí?",
    "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
    "respuesta": "Opción correcta exactamente como aparece en opciones",
    "explicacion": "Breve explicación de por qué es correcta"
  }},
  {{
    "tipo": "abierta",
    "pregunta": "¿Pregunta aquí?",
    "respuesta": "Respuesta esperada completa",
    "explicacion": "Puntos clave que debe incluir la respuesta"
  }}
]"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Responde SOLO con JSON válido, sin texto adicional ni backticks."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.7
        )
        import json
        texto = completion.choices[0].message.content.strip()
        texto = re.sub(r'```json|```', '', texto).strip()
        preguntas = json.loads(texto)
        preguntas_validas = [p for p in preguntas if 'pregunta' in p and 'respuesta' in p and 'tipo' in p]
        return jsonify({'preguntas': preguntas_validas[:num]})
    except Exception as e:
        print(f"ERROR IA QUIZ: {e}")
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
# INICIALIZACIÓN
# ─────────────────────────────────────────────
with app.app_context():
    db.create_all()
    init_gemini()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)