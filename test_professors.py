#!/usr/bin/env python3
"""
Script de teste para verificar a API de professores
"""

import sqlite3
import json

def test_professors_api():
    """Testar se a API de professores está funcionando"""
    
    # Conectar ao banco
    conn = sqlite3.connect('alunos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Verificar se existem professores no banco
    cursor.execute('SELECT id, full_name, role FROM Users WHERE role = "professor" ORDER BY full_name')
    professors = cursor.fetchall()
    
    print("=== TESTE DA API DE PROFESSORES ===")
    print(f"Total de professores encontrados: {len(professors)}")
    
    if professors:
        print("\nProfessores no banco:")
        for prof in professors:
            print(f"  - ID: {prof['id']}, Nome: {prof['full_name']}, Role: {prof['role']}")
        
        # Simular a resposta da API
        professors_dict = [dict(row) for row in professors]
        print(f"\nResposta da API (JSON): {json.dumps(professors_dict, indent=2)}")
    else:
        print("❌ NENHUM PROFESSOR ENCONTRADO!")
        
        # Verificar todos os usuários
        cursor.execute('SELECT id, username, full_name, role FROM Users')
        all_users = cursor.fetchall()
        print(f"\nTodos os usuários no banco ({len(all_users)}):")
        for user in all_users:
            print(f"  - ID: {user['id']}, Username: {user['username']}, Nome: {user['full_name']}, Role: {user['role']}")
    
    conn.close()

if __name__ == "__main__":
    test_professors_api()
