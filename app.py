from flask import Flask, request, jsonify, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)

def conectar_bd():
    conn = sqlite3.connect('alunos.db')
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        # Tabelas são criadas se não existirem
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                numero_matricula TEXT NOT NULL UNIQUE,
                data_matricula TEXT NOT NULL,
                atestados INTEGER NOT NULL,
                encaminhamento TEXT,
                obs TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno_id INTEGER NOT NULL,
                module_id INTEGER NOT NULL,
                faltas INTEGER NOT NULL,
                nota_tutor REAL NOT NULL,
                nota_avaliacao_regular REAL NOT NULL,
                nota_recuperacao REAL NOT NULL,
                nota_final REAL NOT NULL,
                FOREIGN KEY (aluno_id) REFERENCES Alunos(id) ON DELETE CASCADE,
                FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
            )
        ''')
        print("Banco de dados inicializado com sucesso.")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/criar_modulo', methods=['POST'])
def criar_modulo():
    data = request.get_json()
    nome = data.get('nome')

    if not nome:
        return jsonify({'error': 'Nome do módulo é obrigatório'}), 400

    conn = conectar_bd()
    cursor = conn.cursor()
    try:
        # Inserir o módulo na tabela modules
        cursor.execute('INSERT INTO modules (nome) VALUES (?)', (nome,))
        modulo_id = cursor.lastrowid

        # Inserir todos os alunos no novo módulo
        cursor.execute("SELECT id FROM Alunos")
        alunos = cursor.fetchall()
        for aluno in alunos:
            cursor.execute("""
                INSERT INTO module_data (aluno_id, module_id, faltas, nota_tutor, nota_avaliacao_regular, nota_recuperacao, nota_final) 
                VALUES (?, ?, 0, 0, 0, 0, 0)
            """, (aluno['id'], modulo_id))

        conn.commit()
        return jsonify({'message': 'Módulo criado com sucesso e todos os alunos foram adicionados!'}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'Módulo já existe com esse nome.'}), 400
    finally:
        conn.close()

@app.route('/adicionar_aluno', methods=['POST'])
def adicionar_aluno():
    dados = request.get_json()
    nome = dados.get('nome')
    numero_matricula = dados.get('numero_matricula')
    data_matricula = dados.get('data_matricula')
    atestados = dados.get('atestados')
    encaminhamento = dados.get('encaminhamento')
    obs = dados.get('obs')

    if not nome or not numero_matricula or not data_matricula or atestados is None:
        return jsonify({'error': 'Todos os campos obrigatórios devem ser preenchidos.'}), 400

    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        # Adicionar aluno à tabela Alunos
        cursor.execute("""
            INSERT INTO Alunos (nome, numero_matricula, data_matricula, atestados, encaminhamento, obs) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, numero_matricula, data_matricula, atestados, encaminhamento, obs))
        aluno_id = cursor.lastrowid  # Obtenha o ID do aluno adicionado

        # Adicionar o aluno em todos os módulos existentes
        cursor.execute("SELECT id FROM modules")
        modulos = cursor.fetchall()
        for modulo in modulos:
            cursor.execute("""
                INSERT INTO module_data (aluno_id, module_id, faltas, nota_tutor, nota_avaliacao_regular, nota_recuperacao, nota_final) 
                VALUES (?, ?, 0, 0, 0, 0, 0)
            """, (aluno_id, modulo['id']))

        conn.commit()
        return jsonify({'message': 'Aluno adicionado com sucesso em todos os módulos!'}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'Número de matrícula já cadastrado.'}), 400
    finally:
        conn.close()

@app.route('/editar_aluno/<string:numero_matricula>', methods=['PUT'])
def editar_aluno(numero_matricula):
    dados = request.get_json()
    nome = dados.get('nome')
    data_matricula = dados.get('data_matricula')
    atestados = dados.get('atestados')
    encaminhamento = dados.get('encaminhamento')
    obs = dados.get('obs')

    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Alunos WHERE numero_matricula = ?", (numero_matricula,))
    aluno = cursor.fetchone()

    if not aluno:
        conn.close()
        return jsonify({'error': 'Aluno não encontrado.'}), 404

    cursor.execute('''
        UPDATE Alunos
        SET nome = ?, data_matricula = ?, atestados = ?, encaminhamento = ?, obs = ?
        WHERE numero_matricula = ?
    ''', (nome, data_matricula, atestados, encaminhamento, obs, numero_matricula))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Aluno editado com sucesso!'}), 200

@app.route('/excluir_aluno/<string:numero_matricula>', methods=['DELETE'])
def excluir_aluno(numero_matricula):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Alunos WHERE numero_matricula = ?", (numero_matricula,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Aluno não encontrado.'}), 404

    conn.commit()
    conn.close()
    return jsonify({'message': 'Aluno excluído com sucesso!'}), 200

@app.route('/excluir_modulo', methods=['POST'])
def excluir_modulo():
    data = request.get_json()
    nome_modulo = data.get('nome')

    if not nome_modulo:
        return jsonify({'error': 'Nome do módulo é obrigatório para exclusão.'}), 400

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM modules WHERE nome = ?", (nome_modulo,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Módulo não encontrado.'}), 404

    conn.commit()
    conn.close()

    return jsonify({'message': 'Módulo excluído com sucesso!'}), 200

@app.route('/pesquisar_aluno', methods=['GET'])
def pesquisar_aluno():
    numero_matricula = request.args.get('numero_matricula')
    nome = request.args.get('nome')
    conn = conectar_bd()
    cursor = conn.cursor()

    if numero_matricula:
        cursor.execute("SELECT * FROM Alunos WHERE numero_matricula = ?", (numero_matricula,))
        aluno = cursor.fetchone()
        conn.close()
        if not aluno:
            return jsonify({'error': 'Aluno não encontrado.'}), 404
        return jsonify([dict(aluno)])

    elif nome:
        cursor.execute("SELECT * FROM Alunos WHERE nome LIKE ?", ('%' + nome + '%',))
        alunos = cursor.fetchall()
        conn.close()
        if not alunos:
            return jsonify({'error': 'Nenhum aluno encontrado com esse nome.'}), 404
        return jsonify([dict(aluno) for aluno in alunos])

    conn.close()
    return jsonify({'error': 'Forneça o número da matrícula ou o nome para a pesquisa.'}), 400

@app.route('/detalhes_aluno/<int:aluno_id>', methods=['GET'])
def detalhes_aluno(aluno_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Alunos WHERE id = ?", (aluno_id,))
    aluno = cursor.fetchone()

    if not aluno:
        conn.close()
        return jsonify({'error': 'Aluno não encontrado.'}), 404

    cursor.execute('''
        SELECT module_data.*, modules.nome AS module_nome
        FROM module_data
        JOIN modules ON module_data.module_id = modules.id
        WHERE module_data.aluno_id = ?
    ''', (aluno_id,))
    modules = cursor.fetchall()
    conn.close()

    return render_template('detalhes_aluno.html', aluno=aluno, modules=modules)

@app.route('/detalhes_aluno_id/<int:alunoId>')
def detalhes_aluno_id(alunoId):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Alunos WHERE id = ?", (alunoId,))
    aluno = cursor.fetchone()
    conn.close()
    
    if aluno:
        return jsonify({
            'nome': aluno['nome'],
            'numero_matricula': aluno['numero_matricula'],
            'data_matricula': aluno['data_matricula'],
            'atestados': aluno['atestados'],
            'encaminhamento': aluno['encaminhamento'],
            'obs': aluno['obs']
        })
    return jsonify({'error': 'Aluno não encontrado'}), 404

@app.route('/obter_dados_modulo_aluno/<int:aluno_id>/<int:module_id>', methods=['GET'])
def obter_dados_modulo_aluno(aluno_id, module_id):
    conn = conectar_bd()
    cursor = conn.cursor()

    # Obter as informações gerais do aluno
    cursor.execute("SELECT nome, numero_matricula FROM Alunos WHERE id = ?", (aluno_id,))
    aluno = cursor.fetchone()

    # Verifica se o aluno existe
    if not aluno:
        conn.close()
        return jsonify({'error': 'Aluno não encontrado.'}), 404

    # Obter os dados específicos do módulo para esse aluno
    cursor.execute("""
        SELECT faltas, nota_tutor, nota_avaliacao_regular, nota_recuperacao, nota_final 
        FROM module_data 
        WHERE aluno_id = ? AND module_id = ?
    """, (aluno_id, module_id))
    modulo = cursor.fetchone()
    conn.close()

    # Verifica se os dados do módulo foram encontrados
    if not modulo:
        return jsonify({'error': 'Dados do módulo não encontrados para este aluno.'}), 404

    # Retorna os dados do aluno e do módulo juntos
    return jsonify({
        'nome': aluno['nome'],
        'numero_matricula': aluno['numero_matricula'],
        'faltas': modulo['faltas'],
        'nota_tutor': modulo['nota_tutor'],
        'nota_avaliacao_regular': modulo['nota_avaliacao_regular'],
        'nota_recuperacao': modulo['nota_recuperacao'],
        'nota_final': modulo['nota_final']
    })

@app.route('/listar_modulos', methods=['GET'])
def listar_modulos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM modules")
    modulos = cursor.fetchall()
    conn.close()

    modulos_list = [{'id': modulo['id'], 'nome': modulo['nome']} for modulo in modulos]
    return jsonify(modulos_list)

@app.route('/ver_alunos_modulo/<int:module_id>', methods=['GET'])
def ver_alunos_modulo(module_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id, a.nome, a.numero_matricula, md.faltas, md.nota_tutor, md.nota_avaliacao_regular, md.nota_recuperacao, md.nota_final
        FROM Alunos a
        JOIN module_data md ON a.id = md.aluno_id
        WHERE md.module_id = ?
    ''', (module_id,))
    alunos = cursor.fetchall()
    conn.close()

    if alunos:
        return jsonify([{
            'id': aluno['id'],
            'nome': aluno['nome'],
            'numero_matricula': aluno['numero_matricula'],
            'faltas': aluno['faltas'],
            'nota_tutor': aluno['nota_tutor'],
            'nota_avaliacao_regular': aluno['nota_avaliacao_regular'],
            'nota_recuperacao': aluno['nota_recuperacao'],
            'nota_final': aluno['nota_final']
        } for aluno in alunos])
    else:
        return jsonify({'error': 'Nenhum aluno encontrado neste módulo'}), 404

@app.route('/editar_informacoes_modulo/<int:aluno_id>/<int:module_id>', methods=['PUT'])
def editar_informacoes_modulo(aluno_id, module_id):
    dados = request.get_json()

    # Constrói a consulta SQL dinamicamente com base nos campos recebidos
    campos_para_atualizar = []
    valores = []

    if 'faltas' in dados and dados['faltas'] is not None:
        campos_para_atualizar.append("faltas = ?")
        valores.append(dados['faltas'])

    if 'nota_tutor' in dados and dados['nota_tutor'] is not None:
        campos_para_atualizar.append("nota_tutor = ?")
        valores.append(dados['nota_tutor'])

    if 'nota_avaliacao_regular' in dados and dados['nota_avaliacao_regular'] is not None:
        campos_para_atualizar.append("nota_avaliacao_regular = ?")
        valores.append(dados['nota_avaliacao_regular'])

    if 'nota_recuperacao' in dados and dados['nota_recuperacao'] is not None:
        campos_para_atualizar.append("nota_recuperacao = ?")
        valores.append(dados['nota_recuperacao'])

    if 'nota_final' in dados and dados['nota_final'] is not None:
        campos_para_atualizar.append("nota_final = ?")
        valores.append(dados['nota_final'])

    # Se nenhum campo foi fornecido, retorna um erro
    if not campos_para_atualizar:
        return jsonify({'error': 'Nenhum campo foi fornecido para atualização.'}), 400

    # Constrói a consulta SQL dinâmica
    consulta_sql = f"UPDATE module_data SET {', '.join(campos_para_atualizar)} WHERE aluno_id = ? AND module_id = ?"
    valores.extend([aluno_id, module_id])

    # Executa a atualização
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute(consulta_sql, valores)
    conn.commit()
    conn.close()

    return jsonify({'message': 'Dados do módulo atualizados com sucesso!'}), 200

@app.route('/adicionar_modulo_aluno', methods=['POST'])
def adicionar_modulo_aluno():
    data = request.get_json()
    aluno_id = data.get('aluno_id')
    module_id = data.get('module_id')
    faltas = data.get('faltas')
    nota_tutor = data.get('nota_tutor')
    nota_avaliacao_regular = data.get('nota_avaliacao_regular')
    nota_recuperacao = data.get('nota_recuperacao')
    nota_final = data.get('nota_final')

    if not all([aluno_id, module_id, faltas, nota_tutor, nota_avaliacao_regular, nota_recuperacao, nota_final]):
        return jsonify({'error': 'Todos os campos são obrigatórios.'}), 400

    conn = conectar_bd()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO module_data (aluno_id, module_id, faltas, nota_tutor, nota_avaliacao_regular, nota_recuperacao, nota_final)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (aluno_id, module_id, faltas, nota_tutor, nota_avaliacao_regular, nota_recuperacao, nota_final))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'error': 'Erro ao adicionar dados do módulo ao aluno: ' + str(e)}), 400
    conn.close()

    return jsonify({'message': 'Dados do módulo adicionados ao aluno com sucesso!'}), 201

@app.route('/atualizar_informacoes_modulo/<int:aluno_id>/<int:module_id>', methods=['PUT'])
def atualizar_informacoes_modulo(aluno_id, module_id):
    dados = request.get_json()
    faltas = dados.get('faltas')
    nota_tutor = dados.get('nota_tutor')
    nota_avaliacao_regular = dados.get('nota_avaliacao_regular')
    nota_recuperacao = dados.get('nota_recuperacao')
    nota_final = dados.get('nota_final')

    if not all([faltas, nota_tutor, nota_avaliacao_regular, nota_recuperacao, nota_final]):
        return jsonify({'error': 'Todos os campos são obrigatórios.'}), 400

    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE module_data
        SET faltas = ?, nota_tutor = ?, nota_avaliacao_regular = ?, nota_recuperacao = ?, nota_final = ?
        WHERE aluno_id = ? AND module_id = ?
    """, (faltas, nota_tutor, nota_avaliacao_regular, nota_recuperacao, nota_final, aluno_id, module_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Dados do módulo atualizados com sucesso!'}), 200

if __name__ == '__main__':
    inicializar_bd()
    app.run(debug=True)