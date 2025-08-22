from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "period_grade_system_secret_key")

def conectar_bd():
    conn = sqlite3.connect('alunos.db')
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    """Inicializar banco de dados com nova estrutura do period-grade-system"""
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        # Remover tabelas antigas se existirem
        cursor.execute('DROP TABLE IF EXISTS module_data')
        cursor.execute('DROP TABLE IF EXISTS modules')
        cursor.execute('DROP TABLE IF EXISTS Alunos')
        
        # Criar nova estrutura
        # Tabela Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'coordinator', 'professor')),
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela AcademicPeriods
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS AcademicPeriods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                coordinator_id INTEGER NOT NULL,
                start_date DATE,
                end_date DATE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coordinator_id) REFERENCES Users(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela Students
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_number TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                email TEXT,
                academic_period_id INTEGER NOT NULL,
                enrollment_date DATE NOT NULL,
                medical_certificates INTEGER DEFAULT 0,
                referral_info TEXT,
                observations TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (academic_period_id) REFERENCES AcademicPeriods(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela Modules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                professor_id INTEGER NOT NULL,
                academic_period_id INTEGER NOT NULL,
                credits INTEGER DEFAULT 4,
                max_absences INTEGER DEFAULT 10,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (professor_id) REFERENCES Users(id) ON DELETE CASCADE,
                FOREIGN KEY (academic_period_id) REFERENCES AcademicPeriods(id) ON DELETE CASCADE,
                UNIQUE(code, academic_period_id)
            )
        ''')
        
        # Tabela Enrollments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                module_id INTEGER NOT NULL,
                enrollment_date DATE DEFAULT (date('now')),
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'dropped', 'completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE,
                FOREIGN KEY (module_id) REFERENCES Modules(id) ON DELETE CASCADE,
                UNIQUE(student_id, module_id)
            )
        ''')
        
        # Tabela Grades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enrollment_id INTEGER NOT NULL,
                tutor_grade REAL DEFAULT 0.0,
                regular_exam_grade REAL DEFAULT 0.0,
                makeup_exam_grade REAL DEFAULT 0.0,
                final_grade REAL DEFAULT 0.0,
                absences INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enrollment_id) REFERENCES Enrollments(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        print("Banco de dados reestruturado com sucesso!")
        
        # Popular com dados de exemplo
        popular_dados_exemplo(conn)
        
    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        conn.close()

def popular_dados_exemplo(conn):
    """Popular banco com dados de exemplo"""
    cursor = conn.cursor()
    
    # Usuários de exemplo
    usuarios = [
        ('admin', generate_password_hash('admin123'), 'admin', 'Administrador do Sistema', 'admin@escola.com'),
        ('coord1', generate_password_hash('coord123'), 'coordinator', 'Maria Silva Coordenadora', 'maria@escola.com'),
        ('prof1', generate_password_hash('prof123'), 'professor', 'João Santos Professor', 'joao@escola.com'),
        ('prof2', generate_password_hash('prof123'), 'professor', 'Ana Costa Professora', 'ana@escola.com'),
    ]
    
    print("Inserindo usuários de exemplo...")  # Debug log
    
    cursor.executemany('''
        INSERT OR IGNORE INTO Users (username, password_hash, role, full_name, email) 
        VALUES (?, ?, ?, ?, ?)
    ''', usuarios)
    
    # Verificar se os professores foram inseridos
    cursor.execute('SELECT id, username, full_name, role FROM Users WHERE role = "professor"')
    professores_inseridos = cursor.fetchall()
    print(f"Professores inseridos: {professores_inseridos}")  # Debug log
    
    # Períodos acadêmicos
    periodos = [
        ('2024.1 - Primeiro Semestre', 2, '2024-01-15', '2024-06-30', 1),
        ('2024.2 - Segundo Semestre', 2, '2024-07-15', '2024-12-15', 0),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO AcademicPeriods (name, coordinator_id, start_date, end_date, is_active) 
        VALUES (?, ?, ?, ?, ?)
    ''', periodos)
    
    # Estudantes
    estudantes = [
        ('20241001', 'Carlos Eduardo Silva', 'carlos@email.com', 1, '2024-01-15', 0, '', 'Estudante dedicado'),
        ('20241002', 'Fernanda Oliveira', 'fernanda@email.com', 1, '2024-01-15', 2, 'Atendimento especializado', ''),
        ('20241003', 'Pedro Henrique', 'pedro@email.com', 1, '2024-01-16', 1, '', 'Bom desempenho'),
        ('20241004', 'Julia Santos', 'julia@email.com', 1, '2024-01-16', 0, '', ''),
        ('20241005', 'Rafael Costa', 'rafael@email.com', 1, '2024-01-17', 3, 'Acompanhamento médico', 'Problemas de saúde'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO Students (student_number, full_name, email, academic_period_id, enrollment_date, medical_certificates, referral_info, observations) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', estudantes)
    
    # Módulos
    modulos = [
        ('Matemática I', 'MAT101', 3, 1, 4, 10),
        ('Português', 'POR101', 4, 1, 4, 10),
        ('História', 'HIS101', 3, 1, 3, 8),
        ('Ciências', 'CIE101', 4, 1, 4, 10),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO Modules (name, code, professor_id, academic_period_id, credits, max_absences) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', modulos)
    
    # Matrículas (todos os alunos em todos os módulos)
    cursor.execute('SELECT id FROM Students')
    students = cursor.fetchall()
    cursor.execute('SELECT id FROM Modules')
    modules = cursor.fetchall()
    
    matriculas = []
    for student in students:
        for module in modules:
            matriculas.append((student['id'], module['id']))
    
    cursor.executemany('''
        INSERT OR IGNORE INTO Enrollments (student_id, module_id) 
        VALUES (?, ?)
    ''', matriculas)
    
    # Notas de exemplo
    cursor.execute('SELECT id FROM Enrollments')
    enrollments = cursor.fetchall()
    
    import random
    notas = []
    for enrollment in enrollments:
        tutor = round(random.uniform(5.0, 10.0), 1)
        regular = round(random.uniform(4.0, 10.0), 1)
        makeup = round(random.uniform(3.0, 9.0), 1) if regular < 7.0 else 0.0
        final = max(regular, makeup) if makeup > 0 else regular
        absences = random.randint(0, 8)
        
        notas.append((enrollment['id'], tutor, regular, makeup, final, absences))
    
    cursor.executemany('''
        INSERT OR IGNORE INTO Grades (enrollment_id, tutor_grade, regular_exam_grade, makeup_exam_grade, final_grade, absences) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', notas)
    
    conn.commit()
    print("Dados de exemplo populados com sucesso!")

# Decoradores para controle de acesso
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            user_role = session.get('user_role')
            if user_role not in required_roles:
                flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rotas de Autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_name'] = user['full_name']
            session['username'] = user['username']
            
            flash(f'Bem-vindo, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('login'))

# Rota Principal - Dashboard
@app.route('/')
@login_required
def dashboard():
    user_role = session.get('user_role')
    user_id = session.get('user_id')

    conn = conectar_bd()
    cursor = conn.cursor()

    stats = {}
    
    if user_role == 'admin':
        # Estatísticas para administrador
        cursor.execute('SELECT COUNT(*) as total FROM Users')
        stats['total_users'] = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM AcademicPeriods')
        stats['total_periods'] = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM Students')
        stats['total_students'] = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM Modules')
        stats['total_modules'] = cursor.fetchone()['total']
        
    elif user_role == 'coordinator':
        # Estatísticas para coordenador
        cursor.execute('SELECT COUNT(*) as total FROM AcademicPeriods WHERE coordinator_id = ?', (user_id,))
        stats['my_periods'] = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT COUNT(*) as total FROM Students s 
            JOIN AcademicPeriods ap ON s.academic_period_id = ap.id 
            WHERE ap.coordinator_id = ?
        ''', (user_id,))
        stats['my_students'] = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT COUNT(*) as total FROM Modules m 
            JOIN AcademicPeriods ap ON m.academic_period_id = ap.id 
            WHERE ap.coordinator_id = ?
        ''', (user_id,))
        stats['my_modules'] = cursor.fetchone()['total']
        
    elif user_role == 'professor':
        # Estatísticas para professor
        cursor.execute('SELECT COUNT(*) as total FROM Modules WHERE professor_id = ?', (user_id,))
        stats['my_modules'] = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT COUNT(*) as total FROM Enrollments e 
            JOIN Modules m ON e.module_id = m.id 
            WHERE m.professor_id = ?
        ''', (user_id,))
        stats['my_students'] = cursor.fetchone()['total']

        cursor.execute('''
            SELECT COUNT(*) as total FROM Grades g
            JOIN Enrollments e ON g.enrollment_id = e.id
            JOIN Modules m ON e.module_id = m.id
            WHERE m.professor_id = ? AND g.final_grade >= 7.0
        ''', (user_id,))
        stats['approved_students'] = cursor.fetchone()['total']
    
    conn.close()

    return render_template('dashboard.html', stats=stats, user_role=user_role)

# Rotas do Administrador
@app.route('/admin')
@role_required(['admin'])
def admin_panel():
    return render_template('admin/panel.html')

@app.route('/admin/users')
@role_required(['admin'])
def manage_users():
    return render_template('admin/users.html')

@app.route('/admin/periods')
@role_required(['admin'])
def manage_periods():
    return render_template('admin/periods.html')

# Rotas do Coordenador
@app.route('/coordinator')
@role_required(['coordinator'])
def coordinator_panel():
    return render_template('coordinator/panel.html')

@app.route('/coordinator/periods')
@role_required(['coordinator'])
def coordinator_periods():
    return render_template('coordinator/periods.html')

@app.route('/coordinator/period/<int:period_id>')
@role_required(['coordinator'])
def manage_period(period_id):
    return render_template('coordinator/manage_period.html', period_id=period_id)

@app.route('/coordinator/period/<int:period_id>/modules')
@role_required(['coordinator'])
def manage_period_modules(period_id):
    return render_template('coordinator/modules_fixed.html', period_id=period_id)

# Rotas do Professor
@app.route('/professor')
@role_required(['professor'])
def professor_panel():
    return render_template('professor/panel.html')

@app.route('/professor/modules')
@role_required(['professor'])
def professor_modules():
    return render_template('professor/modules.html')

@app.route('/professor/students')
@role_required(['professor'])
def professor_students():
    return render_template('professor/students.html')

@app.route('/modulos')
@login_required
def modulos():
    """Página de gerenciamento de módulos"""
    return render_template('modulos.html')

@app.route('/criar_modulo', methods=['POST'])
@login_required
def criar_modulo():
    """API para criar novo módulo"""
    data = request.get_json()
    nome = data.get('nome', '').strip()
    
    if not nome:
        return jsonify({'error': 'Nome do módulo é obrigatório'}), 400
    
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    conn = conectar_bd()
    cursor = conn.cursor()
    
    try:
        if user_role == 'coordinator':
            # Para coordenadores, criar módulo nos seus períodos
            cursor.execute('SELECT id FROM AcademicPeriods WHERE coordinator_id = ? AND is_active = 1 LIMIT 1', (user_id,))
            period = cursor.fetchone()
            
            if not period:
                conn.close()
                return jsonify({'error': 'Nenhum período ativo encontrado para este coordenador'}), 400
            
            # Gerar código automático para o módulo
            import time
            codigo = f"MOD{int(time.time() % 10000)}"
            
            cursor.execute('''
                INSERT INTO Modules (name, code, professor_id, academic_period_id, credits, max_absences) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, codigo, user_id, period['id'], 4, 10))
            
        elif user_role == 'professor':
            # Para professores, criar módulo nos períodos onde eles lecionam
            cursor.execute('''
                SELECT DISTINCT ap.id FROM AcademicPeriods ap
                JOIN Modules m ON ap.id = m.academic_period_id
                WHERE m.professor_id = ? AND ap.is_active = 1 LIMIT 1
            ''', (user_id,))
            period = cursor.fetchone()
            
            if not period:
                # Se não tem módulos, pegar o primeiro período ativo
                cursor.execute('SELECT id FROM AcademicPeriods WHERE is_active = 1 LIMIT 1')
                period = cursor.fetchone()
                
                if not period:
                    conn.close()
                    return jsonify({'error': 'Nenhum período ativo encontrado'}), 400
            
            # Gerar código automático para o módulo
            import time
            codigo = f"MOD{int(time.time() % 10000)}"
            
            cursor.execute('''
                INSERT INTO Modules (name, code, professor_id, academic_period_id, credits, max_absences) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, codigo, user_id, period['id'], 4, 10))
            
        else:
            conn.close()
            return jsonify({'error': 'Usuário não tem permissão para criar módulos'}), 403
        
        module_id = cursor.lastrowid
        
        # Se houver alunos no período, matriculá-los automaticamente no novo módulo
        cursor.execute('SELECT id FROM Students WHERE academic_period_id = ? AND is_active = 1', (period['id'],))
        students = cursor.fetchall()
        
        for student in students:
            cursor.execute('''
                INSERT OR IGNORE INTO Enrollments (student_id, module_id) 
                VALUES (?, ?)
            ''', (student['id'], module_id))
            
            # Criar registro de notas vazio
            cursor.execute('SELECT id FROM Enrollments WHERE student_id = ? AND module_id = ?', (student['id'], module_id))
            enrollment = cursor.fetchone()
            
            if enrollment:
                cursor.execute('''
                    INSERT OR IGNORE INTO Grades (enrollment_id, tutor_grade, regular_exam_grade, makeup_exam_grade, final_grade, absences) 
                    VALUES (?, 0.0, 0.0, 0.0, 0.0, 0)
                ''', (enrollment['id'],))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Módulo "{nome}" criado com sucesso! {len(students)} alunos foram matriculados automaticamente.',
            'module_id': module_id
        })
        
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'error': 'Erro ao criar módulo. Código pode já existir.'}), 400
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/modulos')
@login_required
def api_modulos():
    """API para listar módulos do usuário"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    conn = conectar_bd()
    cursor = conn.cursor()
    
    if user_role == 'coordinator':
        # Coordenador vê módulos dos seus períodos
        cursor.execute('''
            SELECT m.*, u.full_name as professor_name, ap.name as period_name
            FROM Modules m
            JOIN Users u ON m.professor_id = u.id
            JOIN AcademicPeriods ap ON m.academic_period_id = ap.id
            WHERE ap.coordinator_id = ?
            ORDER BY m.created_at DESC
        ''', (user_id,))
    elif user_role == 'professor':
        # Professor vê seus próprios módulos
        cursor.execute('''
            SELECT m.*, u.full_name as professor_name, ap.name as period_name
            FROM Modules m
            JOIN Users u ON m.professor_id = u.id
            JOIN AcademicPeriods ap ON m.academic_period_id = ap.id
            WHERE m.professor_id = ?
            ORDER BY m.created_at DESC
        ''', (user_id,))
    else:
        # Admin vê todos os módulos
        cursor.execute('''
            SELECT m.*, u.full_name as professor_name, ap.name as period_name
            FROM Modules m
            JOIN Users u ON m.professor_id = u.id
            JOIN AcademicPeriods ap ON m.academic_period_id = ap.id
            ORDER BY m.created_at DESC
        ''')
    
    modules = [dict(row) for row in cursor.fetchall()]
    
    # Adicionar contagem de alunos para cada módulo
    for module in modules:
        cursor.execute('SELECT COUNT(*) as count FROM Enrollments WHERE module_id = ?', (module['id'],))
        module['student_count'] = cursor.fetchone()['count']
    
    conn.close()
    return jsonify(modules)

@app.route('/professor/module/<int:module_id>')
@role_required(['professor'])
def manage_grades(module_id):
    return render_template('professor/grades.html', module_id=module_id)

# API Routes
@app.route('/api/users', methods=['GET', 'POST'])
@role_required(['admin'])
def api_users():
    conn = conectar_bd()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT id, username, role, full_name, email, created_at FROM Users ORDER BY full_name')
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(users)
    
    elif request.method == 'POST':
        data = request.get_json()
        try:
            cursor.execute('''
                INSERT INTO Users (username, password_hash, role, full_name, email) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data['username'],
                generate_password_hash(data['password']),
                data['role'],
                data['full_name'],
                data['email']
            ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Usuário criado com sucesso!'}), 201
        except sqlite3.IntegrityError as e:
            conn.close()
            return jsonify({'error': 'Usuário ou email já existe.'}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@role_required(['admin'])
def api_user(user_id):
    conn = conectar_bd()
    cursor = conn.cursor()

    if request.method == 'PUT':
        data = request.get_json()
        try:
            if 'password' in data and data['password']:
                cursor.execute('''
                    UPDATE Users SET username=?, password_hash=?, role=?, full_name=?, email=? 
                    WHERE id=?
                ''', (
                    data['username'],
                    generate_password_hash(data['password']),
                    data['role'],
                    data['full_name'],
                    data['email'],
                    user_id
                ))
            else:
                cursor.execute('''
                    UPDATE Users SET username=?, role=?, full_name=?, email=? 
                    WHERE id=?
                ''', (
                    data['username'],
                    data['role'],
                    data['full_name'],
                    data['email'],
                    user_id
                ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Usuário atualizado com sucesso!'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Usuário ou email já existe.'}), 400
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM Users WHERE id=?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Usuário excluído com sucesso!'})

@app.route('/api/periods', methods=['GET', 'POST'])
@role_required(['admin'])
def api_periods():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT p.*, u.full_name as coordinator_name 
            FROM AcademicPeriods p 
            JOIN Users u ON p.coordinator_id = u.id 
            ORDER BY p.created_at DESC
        ''')
        periods = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(periods)

    elif request.method == 'POST':
        data = request.get_json()
        try:
            cursor.execute('''
                INSERT INTO AcademicPeriods (name, coordinator_id, start_date, end_date, is_active) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['coordinator_id'],
                data['start_date'],
                data['end_date'],
                data.get('is_active', 1)
            ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Período acadêmico criado com sucesso!'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Nome do período já existe.'}), 400

# API do Coordenador
@app.route('/api/coordinator/periods')
@role_required(['coordinator'])
def api_coordinator_periods():
    user_id = session.get('user_id')
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM AcademicPeriods WHERE coordinator_id = ? ORDER BY created_at DESC', (user_id,))
    periods = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(periods)

@app.route('/api/periods/<int:period_id>/students', methods=['GET', 'POST'])
@role_required(['coordinator'])
def api_period_students(period_id):
    conn = conectar_bd()
    cursor = conn.cursor()

    # Verificar se o coordenador tem acesso a este período
    user_id = session.get('user_id')
    cursor.execute('SELECT * FROM AcademicPeriods WHERE id = ? AND coordinator_id = ?', (period_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Acesso negado.'}), 403
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM Students WHERE academic_period_id = ? ORDER BY full_name', (period_id,))
        students = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(students)
    
    elif request.method == 'POST':
        data = request.get_json()
        try:
            cursor.execute('''
                INSERT INTO Students (student_number, full_name, email, academic_period_id, enrollment_date, medical_certificates, referral_info, observations) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['student_number'],
                data['full_name'],
                data.get('email', ''),
                period_id,
                data['enrollment_date'],
                data.get('medical_certificates', 0),
                data.get('referral_info', ''),
                data.get('observations', '')
            ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Estudante criado com sucesso!'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Número de matrícula já existe.'}), 400

# API do Professor
@app.route('/api/professor/modules')
@role_required(['professor'])
def api_professor_modules():
    user_id = session.get('user_id')
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, ap.name as period_name 
        FROM Modules m 
        JOIN AcademicPeriods ap ON m.academic_period_id = ap.id 
        WHERE m.professor_id = ? 
        ORDER BY ap.name, m.name
    ''', (user_id,))
    modules = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(modules)

@app.route('/api/modules/<int:module_id>/students')
@role_required(['professor'])
def api_module_students(module_id):
    user_id = session.get('user_id')
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Verificar se o professor tem acesso a este módulo
    cursor.execute('SELECT * FROM Modules WHERE id = ? AND professor_id = ?', (module_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Acesso negado.'}), 403
    
    cursor.execute('''
        SELECT s.*, e.id as enrollment_id, e.status, 
               g.tutor_grade, g.regular_exam_grade, g.makeup_exam_grade, g.final_grade, g.absences 
        FROM Students s 
        JOIN Enrollments e ON s.id = e.student_id 
        LEFT JOIN Grades g ON e.id = g.enrollment_id 
        WHERE e.module_id = ? 
        ORDER BY s.full_name
    ''', (module_id,))
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(students)

@app.route('/api/grades/<int:enrollment_id>', methods=['PUT'])
@role_required(['professor'])
def api_update_grades(enrollment_id):
    user_id = session.get('user_id')
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Verificar se o professor tem acesso a esta matrícula
    cursor.execute('''
        SELECT e.* FROM Enrollments e 
        JOIN Modules m ON e.module_id = m.id 
        WHERE e.id = ? AND m.professor_id = ?
    ''', (enrollment_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Acesso negado.'}), 403

    data = request.get_json()
    
    # Verificar se já existe registro de notas
    cursor.execute('SELECT * FROM Grades WHERE enrollment_id = ?', (enrollment_id,))
    existing_grade = cursor.fetchone()
    
    if existing_grade:
        cursor.execute('''
            UPDATE Grades SET tutor_grade=?, regular_exam_grade=?, makeup_exam_grade=?, final_grade=?, absences=?, last_updated=CURRENT_TIMESTAMP 
            WHERE enrollment_id=?
        ''', (
            data['tutor_grade'],
            data['regular_exam_grade'],
            data['makeup_exam_grade'],
            data['final_grade'],
            data['absences'],
            enrollment_id
        ))
    else:
        cursor.execute('''
            INSERT INTO Grades (enrollment_id, tutor_grade, regular_exam_grade, makeup_exam_grade, final_grade, absences) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            enrollment_id,
            data['tutor_grade'],
            data['regular_exam_grade'],
            data['makeup_exam_grade'],
            data['final_grade'],
            data['absences']
        ))
    
    conn.commit()
    conn.close()

    return jsonify({'message': 'Notas atualizadas com sucesso!'})

@app.route('/api/professor/students/<int:student_id>/absences', methods=['GET', 'PUT'])
@role_required(['professor'])
def api_professor_absences(student_id):
    """API para professores visualizarem e atualizarem faltas de um aluno"""
    user_id = session.get('user_id')
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Verificar se o professor tem acesso a este aluno
    cursor.execute('''
        SELECT s.* FROM Students s 
        JOIN Enrollments e ON s.id = e.student_id
        JOIN Modules m ON e.module_id = m.id
        WHERE s.id = ? AND m.professor_id = ?
    ''', (student_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Acesso negado.'}), 403

    if request.method == 'GET':
        # Buscar faltas do aluno nos módulos do professor
        cursor.execute('''
            SELECT AVG(g.absences) as avg_absences, MAX(g.absences) as max_absences
            FROM Grades g
            JOIN Enrollments e ON g.enrollment_id = e.id
            JOIN Modules m ON e.module_id = m.id
            WHERE e.student_id = ? AND m.professor_id = ?
        ''', (student_id, user_id))
        result = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'absences': int(result['avg_absences'] or 0),
            'max_absences': int(result['max_absences'] or 0)
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Atualizar faltas em todas as matrículas do aluno nos módulos do professor
        cursor.execute('''
            UPDATE Grades SET absences = ?, last_updated = CURRENT_TIMESTAMP
            WHERE enrollment_id IN (
                SELECT e.id FROM Enrollments e
                JOIN Modules m ON e.module_id = m.id
                WHERE e.student_id = ? AND m.professor_id = ?
            )
        ''', (data['absences'], student_id, user_id))
        
        conn.commit()
        conn.close()

        return jsonify({'message': 'Faltas atualizadas com sucesso!'})

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

@app.route('/test/professors')
def test_professors_page():
    """Página de teste para verificar a API de professores"""
    return render_template('test_professors.html')

@app.route('/api/coordinators')
@role_required(['admin'])
def api_coordinators():
    """API para buscar coordenadores disponíveis"""
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name FROM Users WHERE role = "coordinator" ORDER BY full_name')
    coordinators = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(coordinators)

# API para o coordenador adicionar módulos
@app.route('/api/coordinator/periods/<int:period_id>/modules', methods=['GET', 'POST'])
@role_required(['coordinator'])
def api_coordinator_modules(period_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Verificar se o coordenador tem acesso a este período
    user_id = session.get('user_id')
    cursor.execute('SELECT * FROM AcademicPeriods WHERE id = ? AND coordinator_id = ?', (period_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Acesso negado.'}), 403
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT m.*, u.full_name as professor_name 
            FROM Modules m 
            JOIN Users u ON m.professor_id = u.id 
            WHERE m.academic_period_id = ? 
            ORDER BY m.name
        ''', (period_id,))
        modules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(modules)
    
    elif request.method == 'POST':
        data = request.get_json()
        try:
            cursor.execute('''
                INSERT INTO Modules (name, code, professor_id, academic_period_id, credits, max_absences) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['code'],
                data['professor_id'],
                period_id,
                data.get('credits', 4),
                data.get('max_absences', 10)
            ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Módulo criado com sucesso!'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Código do módulo já existe neste período.'}), 400

# API para o coordenador editar informações dos alunos
@app.route('/api/coordinator/students/<int:student_id>', methods=['PUT', 'DELETE'])
@role_required(['coordinator'])
def api_coordinator_edit_student(student_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Verificar se o coordenador tem acesso a este aluno
    user_id = session.get('user_id')
    cursor.execute('''
        SELECT s.* FROM Students s 
        JOIN AcademicPeriods ap ON s.academic_period_id = ap.id 
        WHERE s.id = ? AND ap.coordinator_id = ?
    ''', (student_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Acesso negado.'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        try:
            cursor.execute('''
                UPDATE Students SET 
                    student_number=?, full_name=?, email=?, enrollment_date=?, 
                    medical_certificates=?, referral_info=?, observations=?
                WHERE id=?
            ''', (
                data['student_number'],
                data['full_name'],
                data.get('email', ''),
                data['enrollment_date'],
                data.get('medical_certificates', 0),
                data.get('referral_info', ''),
                data.get('observations', ''),
                student_id
            ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Informações do estudante atualizadas com sucesso!'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Número de matrícula já existe.'}), 400
    
    elif request.method == 'DELETE':
        try:
            cursor.execute('DELETE FROM Students WHERE id = ?', (student_id,))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Estudante excluído com sucesso!'})
        except sqlite3.Error as e:
            conn.close()
            return jsonify({'error': 'Erro ao excluir estudante.'}), 500

# API para buscar professores disponíveis
@app.route('/api/coordinator/professors')
@role_required(['coordinator'])
def api_coordinator_professors():
    """API para buscar professores disponíveis"""
    print(f"API chamada por usuário: {session.get('user_id')}, role: {session.get('user_role')}")  # Debug log
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name FROM Users WHERE role = "professor" ORDER BY full_name')
    professors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    print(f"Professores encontrados: {professors}")  # Debug log
    return jsonify(professors)

# API para professores gerenciarem alunos
@app.route('/api/professor/students', methods=['GET', 'POST'])
@role_required(['professor'])
def api_professor_students():
    """API para professores gerenciarem alunos"""
    user_id = session.get('user_id')
    conn = conectar_bd()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        # Buscar alunos dos módulos do professor
        cursor.execute('''
            SELECT DISTINCT s.*, ap.name as period_name
            FROM Students s 
            JOIN AcademicPeriods ap ON s.academic_period_id = ap.id
            JOIN Enrollments e ON s.id = e.student_id
            JOIN Modules m ON e.module_id = m.id
            WHERE m.professor_id = ?
            ORDER BY s.full_name
        ''', (user_id,))
        students = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(students)
    
    elif request.method == 'POST':
        data = request.get_json()
        print(f"[DEBUG] Dados recebidos para criação de aluno: {data}")  # Debug log
        try:
            # Verificar se o período existe e está ativo
            cursor.execute('SELECT id FROM AcademicPeriods WHERE id = ? AND is_active = 1', (data['academic_period_id'],))
            period_check = cursor.fetchone()
            print(f"[DEBUG] Verificação de período - ID: {data['academic_period_id']}, Encontrado: {period_check}")  # Debug log
            if not period_check:
                conn.close()
                return jsonify({'error': 'Período acadêmico não encontrado ou inativo.'}), 400
            
            # Inserir novo aluno
            cursor.execute('''
                INSERT INTO Students (student_number, full_name, email, academic_period_id, enrollment_date, medical_certificates, referral_info, observations) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['student_number'],
                data['full_name'],
                data.get('email', ''),
                data['academic_period_id'],
                data['enrollment_date'],
                data.get('medical_certificates', 0),
                data.get('referral_info', ''),
                data.get('observations', '')
            ))
            
            student_id = cursor.lastrowid
            print(f"[DEBUG] Aluno criado com ID: {student_id}")  # Debug log
            
            # Matricular o aluno nos módulos do professor (se existirem)
            cursor.execute('SELECT id FROM Modules WHERE professor_id = ? AND academic_period_id = ?', (user_id, data['academic_period_id']))
            modules = cursor.fetchall()
            print(f"[DEBUG] Módulos encontrados para matricular: {modules}")  # Debug log
            
            if modules:
                for module in modules:
                    cursor.execute('''
                        INSERT OR IGNORE INTO Enrollments (student_id, module_id) 
                        VALUES (?, ?)
                    ''', (student_id, module['id']))
                    
                    # Buscar o ID da matrícula criada
                    cursor.execute('SELECT id FROM Enrollments WHERE student_id = ? AND module_id = ?', (student_id, module['id']))
                    enrollment = cursor.fetchone()
                    
                    if enrollment:
                        # Criar registro de notas vazio
                        cursor.execute('''
                            INSERT OR IGNORE INTO Grades (enrollment_id, tutor_grade, regular_exam_grade, makeup_exam_grade, final_grade, absences) 
                            VALUES (?, 0.0, 0.0, 0.0, 0.0, 0)
                        ''', (enrollment['id'],))
            else:
                print(f"[DEBUG] Nenhum módulo encontrado para o professor {user_id} no período {data['academic_period_id']}")  # Debug log
            
            conn.commit()
            print(f"[DEBUG] Transação commitada com sucesso!")  # Debug log
            conn.close()
            
            if modules:
                return jsonify({'message': f'Aluno criado e matriculado em {len(modules)} módulo(s) com sucesso!'}), 201
            else:
                return jsonify({'message': 'Aluno criado com sucesso! (Ainda não há módulos para matricular)'}), 201
        except sqlite3.IntegrityError as e:
            print(f"[DEBUG] Erro de integridade: {e}")  # Debug log
            conn.close()
            return jsonify({'error': 'Número de matrícula já existe.'}), 400
        except Exception as e:
            print(f"[DEBUG] Erro inesperado: {e}")  # Debug log
            conn.close()
            return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/professor/students/<int:student_id>', methods=['GET', 'PUT'])
@role_required(['professor'])
def api_professor_student_detail(student_id):
    """API para professores visualizarem e editarem informações dos alunos"""
    user_id = session.get('user_id')
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Verificar se o professor tem acesso a este aluno
    cursor.execute('''
        SELECT s.* FROM Students s 
        JOIN Enrollments e ON s.id = e.student_id
        JOIN Modules m ON e.module_id = m.id
        WHERE s.id = ? AND m.professor_id = ?
    ''', (student_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Acesso negado.'}), 403
    
    if request.method == 'GET':
        # Buscar dados completos do aluno
        cursor.execute('''
            SELECT s.*, ap.name as period_name
            FROM Students s 
            JOIN AcademicPeriods ap ON s.academic_period_id = ap.id
            WHERE s.id = ?
        ''', (student_id,))
        student = dict(cursor.fetchone())
        conn.close()
        return jsonify(student)
    
    elif request.method == 'PUT':
        data = request.get_json()
        try:
            cursor.execute('''
                UPDATE Students SET 
                    student_number=?, full_name=?, email=?, enrollment_date=?, 
                    medical_certificates=?, referral_info=?, observations=?
                WHERE id=?
            ''', (
                data['student_number'],
                data['full_name'],
                data.get('email', ''),
                data['enrollment_date'],
                data.get('medical_certificates', 0),
                data.get('referral_info', ''),
                data.get('observations', ''),
                student_id
            ))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Informações do aluno atualizadas com sucesso!'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Número de matrícula já existe.'}), 400

@app.route('/api/professor/periods')
@role_required(['professor'])
def api_professor_periods():
    """API para professores buscarem períodos disponíveis"""
    user_id = session.get('user_id')
    print(f"[DEBUG] Buscando períodos para professor ID: {user_id}")  # Debug log
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT ap.* FROM AcademicPeriods ap
        JOIN Modules m ON ap.id = m.academic_period_id
        WHERE m.professor_id = ? AND ap.is_active = 1
        ORDER BY ap.name
    ''', (user_id,))
    periods = [dict(row) for row in cursor.fetchall()]
    print(f"[DEBUG] Períodos encontrados: {periods}")  # Debug log
    conn.close()
    
    return jsonify(periods)

# API alternativa para períodos (mais permissiva)
@app.route('/api/periods')
@login_required
def api_periods_alternative():
    """API para buscar todos os períodos ativos (mais permissiva)"""
    print(f"[DEBUG] API alternativa de períodos chamada por usuário: {session.get('user_id')}")  # Debug log
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM AcademicPeriods WHERE is_active = 1 ORDER BY name')
    periods = [dict(row) for row in cursor.fetchall()]
    print(f"[DEBUG] Todos os períodos ativos encontrados: {periods}")  # Debug log
    conn.close()
    
    return jsonify(periods)

# API alternativa para professores (mais permissiva)
@app.route('/api/professors')
def api_professors():
    """API para buscar professores (sem restrição de role)"""
    print(f"API alternativa chamada por usuário: {session.get('user_id')}, role: {session.get('user_role')}")  # Debug log
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('SELECT id, full_name FROM Users WHERE role = "professor" ORDER BY full_name')
        professors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        print(f"Professores encontrados (API alternativa): {professors}")  # Debug log
        return jsonify(professors)
    except Exception as e:
        print(f"Erro na API de professores: {e}")  # Debug log
        return jsonify({'error': str(e)}), 500

# API temporária para teste (sem autenticação)
@app.route('/api/test/professors')
def api_test_professors():
    """API temporária para teste de professores"""
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name FROM Users WHERE role = "professor" ORDER BY full_name')
    professors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    print(f"API de teste - Professores encontrados: {professors}")  # Debug log
    return jsonify(professors)

if __name__ == '__main__':
    inicializar_bd()
    app.run(debug=True)