# Aplicação Professor

## Descrição da Aplicação

A Aplicação Professor é um sistema desenvolvido em Flask para gestão de alunos e módulos acadêmicos. A aplicação inclui funcionalidades como:

- Cadastro, edição e exclusão de alunos.
- Criação e gestão de módulos.
- Consulta e edição de informações acadêmicas.
- Integração com um banco de dados SQLite.
- Deployment local e remoto, com suporte a Kubernetes.

## Configuração do Ambiente Local

### Requisitos:
- Python 3.10 ou superior.
- Docker e Docker Compose.
- Git.

### Passos:

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/P4d1lh4/Aplica-o-Professor.git
   cd Aplica-o-Professor
   ```

2. **Crie um arquivo `.env`:**
   Crie o arquivo na raiz do projeto e adicione:
   ```env
   FLASK_SECRET_KEY=uma_chave_segura_aqui
   ```

3. **Instale as dependências:**
   Ative o ambiente virtual (opcional) e instale as dependências do projeto:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Inicie o servidor localmente:**
   ```bash
   flask run --host=0.0.0.0
   ```
   Acesse a aplicação em `http://localhost:5000`.

5. **Usando Docker Compose:**
   Para iniciar a aplicação com Docker Compose:
   ```bash
   docker-compose up --build
   ```

## Deployment em Ambientes Remotos

### Opção 1: Servidor com Docker Compose

1. Configure um servidor remoto com Docker e Docker Compose instalados.
2. Adicione as credenciais do servidor remoto no repositório GitHub como secrets:
   - `REMOTE_HOST` (IP do servidor remoto).
   - `REMOTE_USER` (usuário do servidor).
   - `REMOTE_SSH_KEY` (chave privada para acesso SSH).
3. Atualize o arquivo `deploy.yml` para refletir o caminho do projeto no servidor.

O pipeline CI/CD fará o deployment automaticamente ao realizar push na branch `main`.

### Opção 2: Kubernetes

1. Certifique-se de que o cluster Kubernetes está configurado.
2. Aplique o arquivo `deployment.yaml` ao cluster:
   ```bash
   kubectl apply -f deployment.yaml
   ```
3. Acesse a aplicação pelo LoadBalancer ou pelo Ingress configurado.

## Pipeline de CI/CD

O projeto utiliza GitHub Actions para automatizar testes e deployment:

- **Etapa de Build:**
  - Instala dependências.
  - Executa testes com `pytest`.
  - Analisa o código com `bandit` para identificar vulnerabilidades.

- **Etapa de Deployment:**
  - Faz pull do repositório no servidor remoto.
  - Reinicia os containers com Docker Compose.

Pipeline configurado no arquivo `deploy.yml`.

## Deployment em Kubernetes

O arquivo `deployment.yaml` configura:
- Um deployment com 2 réplicas da aplicação.
- Um serviço LoadBalancer para expor a aplicação.
- Montagem de volume para persistência do banco de dados.

### Passos para Testar:
1. Inicie um cluster Kubernetes local (e.g., com `minikube` ou `kind`).
2. Aplique os manifests Kubernetes:
   ```bash
   kubectl apply -f deployment.yaml
   ```
3. Verifique o status dos pods:
   ```bash
   kubectl get pods
   ```
4. Obtenha o IP do LoadBalancer e acesse a aplicação.

---

Com essas instruções, você pode configurar, testar e fazer o deployment da Aplicação Professor em diferentes ambientes.

