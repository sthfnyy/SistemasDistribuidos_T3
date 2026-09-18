# Sistemas Distribuídos - Trabalho 03
## Sistema Cliente/Servidor em Camadas para Processamento de Áudio

Sistema distribuído completo em 3 camadas (Cliente Desktop GUI, Servidor de Aplicação REST e Banco de Dados Relacional) para envio, processamento com FFmpeg, armazenamento estruturado em disco e gestão de metadados.

---

## 🏛️ Arquitetura do Sistema (3 Camadas)

```text
┌─────────────────────────────────────────────────────────┐
│              CAMADA 1: CLIENTE (PySide6)                │
│  - Interface Gráfica Desktop (Qt / PySide6)             │
│  - Seleção de arquivos e leitura local de metadados     │
│  - Configuração de operações e parâmetros de áudio      │
│  - Player de áudio embutido (Original e Processado)     │
│  - Visualizador de forma de onda (waveform.png)         │
│  - Histórico interativo sincronizado via API            │
└───────────────────────────┬─────────────────────────────┘
                            │
                      HTTP / REST API
                            │
┌───────────────────────────▼─────────────────────────────┐
│              CAMADA 2: SERVIDOR (FastAPI)               │
│  - API REST assíncrona (Recebimento, Streaming, Busca)  │
│  - Motor de processamento FFmpeg                        │
│    (Normalização, Mono, Velocidade, Bitrate, Formato)   │
│  - Gerador automático de formas de onda (waveform.png)  │
│  - Armazenamento em disco por Data e UUID               │
│    storage/{YYYY}/{MM}/{DD}/{UUID}/                     │
│  - Geração de meta.json com Checksums SHA-256           │
│  - Gestão de exclusão com pasta storage/trash/          │
│  - Interface Web simples para navegador (HTML5 Audio)   │
└───────────────────────────┬─────────────────────────────┘
                            │
                       SQLAlchemy
                            │
┌───────────────────────────▼─────────────────────────────┐
│             CAMADA 3: BANCO DE DADOS (PostgreSQL)       │
│  - Tabela 'audios' com metadados técnicos dos arquivos  │
│  - Duração, bitrate, taxa de amostragem, canais, paths  │
└─────────────────────────────────────────────────────────┘
```

---

## 👥 Divisão de Responsabilidades

| Participante | Camadas e Escopo de Desenvolvimento |
|---|---|
| **Pessoa 1** | **Cliente Desktop (PySide6)**: Interface gráfica, leitura local de arquivos (`mutagen`), player duplo de áudio, visualizador de waveform, módulo HTTP cliente (`requests`), histórico interativo e documentação do cliente. |
| **Pessoa 2** | **Servidor, FFmpeg e Banco (FastAPI + PostgreSQL)**: API REST, integração FFmpeg, extração com ffprobe, geração de waveform, armazenamento físico por data/UUID, `meta.json`, `trash/`, banco PostgreSQL com SQLAlchemy e interface web simples. |

---

## 🚀 Como Executar o Projeto

### 1. Iniciar o Banco de Dados PostgreSQL (Docker Compose)
```bash
docker compose up -d
```
*O PostgreSQL subirá no container `audio_postgres` na porta `5434` (mapeada para `5432` internamente) com banco `audiodb`, usuário `postgres` e senha `postgres`.*

### 2. Configurar o Ambiente Virtual Python
```bash
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências do servidor e do cliente
pip install -r server/requirements.txt
pip install -r client/requirements.txt
```

### 3. Executar o Servidor FastAPI (Camada 2)
```bash
python server/run_server.py
```
Acessos úteis:
- **Interface Web de Arquivos:** [http://localhost:8000/files](http://localhost:8000/files)
- **Documentação da API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentação ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 4. Executar o Cliente Desktop PySide6 (Camada 1)
Em outro terminal (com o ambiente virtual ativado):
```bash
python client/main.py
```

> **Para executar entre dois computadores distintos:**
> Configure o IP da máquina do servidor na máquina cliente antes de abrir a interface:
> ```bash
> export SERVER_HOST="192.168.X.Y"
> export SERVER_PORT=8000
> python client/main.py
> ```

### 5. Executar Todos os Testes Automatizados
```bash
pytest -v
```

---

## 📂 Organização do Armazenamento no Servidor

Conforme especificado no trabalho, cada áudio processado é armazenado em subpastas estruturadas por ano, mês, dia e UUID único:

```text
server/storage/
├── 2026/
│   └── 09/
│       └── 16/
│           └── 8f3c7e8e-4a0b-4d7a-8f1b-3ef5a95f2d01/
│               ├── audio_original.mp3    # Áudio original enviado
│               ├── audio_processed.mp3   # Áudio resultante do processamento
│               ├── meta.json             # Checksums SHA-256 e parâmetros
│               └── waveform.png          # Visualização gráfica da forma de onda
└── trash/                                # Lixeira para arquivos excluídos
```

---

## 📋 Endpoints da API REST

- `POST /process-audio` (ou `POST /audios/process`): Envio de áudio (`multipart/form-data`) + tipo de processamento.
- `GET /audios` (ou `GET /history`): Histórico de áudios cadastrados no banco.
- `GET /audio/{uuid}`: Detalhes e metadados de um áudio específico.
- `GET /audio/{uuid}/original`: Streaming/download do áudio original.
- `GET /audio/{uuid}/processed`: Streaming/download do áudio processado.
- `GET /audio/{uuid}/waveform`: Imagem PNG da forma de onda.
- `GET /audio/{uuid}/meta`: Metadados complementares (`meta.json`).
- `DELETE /audio/{uuid}`: Move arquivos para `trash/` e atualiza status no banco.
- `GET /files`: Página web HTML com listagem e reprodução direta no navegador.
