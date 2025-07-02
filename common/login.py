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
            admin_password = self.hash_password("admin123")
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
        conn.close()
        
        if resultado:
            return {
                'id': resultado[0],
                'nombre': resultado[1],
                'rol': resultado[2],
                'usuario': usuario
            }
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
                    # Guardar en session_state
                    st.session_state.authenticated = True
                    st.session_state.user_data = user_data
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
        - Contraseña: `admin123`
        """)
    
    def logout(self):
        """Cierra la sesión del usuario"""
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.rerun()
    
    def is_authenticated(self):
        """Verifica si el usuario está autenticado"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self):
        """Obtiene los datos del usuario actual"""
        return st.session_state.get('user_data', None)