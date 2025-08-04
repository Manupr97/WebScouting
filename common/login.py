# common/login.py - VERSIÓN COMPLETA MEJORADA

import streamlit as st
import hashlib
import sqlite3
import os
from datetime import datetime, timedelta

class LoginManager:
    def __init__(self, db_path="data/usuarios.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos de usuarios"""
        # Crear carpeta data si no existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT,
                rol TEXT DEFAULT 'analista',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_acceso TIMESTAMP
            )
        ''')
        
        # Crear tabla de sesiones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sesiones (
                token TEXT PRIMARY KEY,
                usuario_id INTEGER,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Crear usuario admin por defecto si no existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = ?", ("admin",))
        if cursor.fetchone()[0] == 0:
            admin_password = self.hash_password("admin")
            cursor.execute('''
                INSERT INTO usuarios (usuario, password, nombre, email, rol)
                VALUES (?, ?, ?, ?, ?)
            ''', ("admin", admin_password, "Administrador", "admin@scoutingpro.com", "admin"))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Encripta la contraseña"""
        return hashlib.sha256(str(password).encode()).hexdigest()
    
    def verificar_credenciales(self, usuario, password):
        """Verifica las credenciales del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, nombre, rol FROM usuarios 
            WHERE usuario = ? AND password = ?
        ''', (usuario, password_hash))
        
        resultado = cursor.fetchone()
        
        # Actualizar último acceso
        if resultado:
            cursor.execute('''
                UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP
                WHERE usuario = ?
            ''', (usuario,))
            conn.commit()
        
        conn.close()
        
        if resultado:
            # IMPORTANTE: Guardar en AMBOS formatos para máxima compatibilidad
            # Formato 1: Campos individuales (para partido_model.py)
            st.session_state.authenticated = True
            st.session_state.usuario = usuario
            st.session_state.nombre = resultado[1]
            st.session_state.rol = resultado[2]
            st.session_state.user_id = resultado[0]
            
            # Formato 2: Diccionario user_data (para mantener compatibilidad)
            user_data = {
                'id': resultado[0],
                'nombre': resultado[1],
                'rol': resultado[2],
                'usuario': usuario
            }
            st.session_state.user_data = user_data
            
            return user_data
        return None
    
    def mostrar_login(self):
        """Muestra el formulario de login"""
        st.markdown("""
            <div style='text-align: center; padding: 2rem;'>
                <h1>🔐 Acceso a Scouting Pro</h1>
                <p>Introduce tus credenciales para acceder</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                usuario = st.text_input("👤 Usuario", placeholder="Introduce tu usuario")
                password = st.text_input("🔒 Contraseña", type="password", placeholder="Introduce tu contraseña")
                submit_button = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
        
        if submit_button:
            if usuario and password:
                user_data = self.verificar_credenciales(usuario, password)
                if user_data:
                    st.success(f"¡Bienvenido/a, {user_data['nombre']}!")
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
            else:
                st.warning("⚠️ Por favor, completa todos los campos")
        
        # Información de prueba
        st.markdown("---")
        st.info("""
        **🧪 Credenciales de prueba:**
        - Usuario: `admin`
        - Contraseña: `admin`
        """)
    
    def logout(self):
        """Cierra la sesión del usuario"""
        # Limpiar TODOS los datos de sesión
        keys_to_remove = ['authenticated', 'user_data', 'usuario', 'nombre', 'rol', 'user_id']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    def is_authenticated(self):
        """Verifica si el usuario está autenticado"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self):
        """Obtiene los datos del usuario actual - COMPATIBLE CON AMBOS FORMATOS"""
        if st.session_state.get('authenticated', False):
            # Intentar primero con user_data (formato nuevo)
            if 'user_data' in st.session_state and st.session_state.user_data:
                return st.session_state.user_data
            # Si no, construir desde campos individuales (formato antiguo)
            elif 'usuario' in st.session_state:
                return {
                    'id': st.session_state.get('user_id', 0),
                    'usuario': st.session_state.usuario,
                    'nombre': st.session_state.nombre,
                    'rol': st.session_state.rol
                }
        return None
    
    def get_user_role(self):
        """Obtiene el rol del usuario actual"""
        user = self.get_current_user()
        return user['rol'] if user else None
    
    def is_admin(self):
        """Verifica si el usuario actual es administrador"""
        return self.get_user_role() == 'admin'
    
    def require_auth(self):
        """Decorator para requerir autenticación en páginas"""
        if not self.is_authenticated():
            st.error("🔒 Debes iniciar sesión para acceder a esta página")
            st.stop()
    
    def require_admin(self):
        """Decorator para requerir rol de administrador"""
        self.require_auth()
        if not self.is_admin():
            st.error("🔒 Esta página requiere permisos de administrador")
            st.stop()