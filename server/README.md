# Servidor de Processamento de Áudio (Pessoa 2)

Serviço backend construído com **FastAPI**, **FFmpeg**, **PostgreSQL** e **SQLAlchemy** para recepção, processamento, armazenamento estruturado e transmissão de áudios em arquitetura cliente/servidor de 3 camadas.

---

## 1. Arquitetura e Estrutura de Diretórios

```text
server/
├── app/
│   ├── main.py              # Ponto de entrada FastAPI e ciclo de vida
│   ├── config.py            # Configurações com Pydantic Settings
│   ├── schemas.py           # Modelos Pydantic de validação e serialização
│   ├── database/
│   │   ├── connection.py    # Conexão SQLAlchemy e engine com pool
│   │   └── models.py        # Modelo ORM da tabela 'audios'
│   ├── routes/
│   │   ├── audio.py         # Endpoints de envio, download, streaming e exclusão
│   │   ├── history.py       # Endpoints de consulta de histórico
│   │   └── web.py           # Rota da interface web HTML5
│   ├── services/
│   │   ├── ffmpeg.py        # Processamento de áudio e extração com ffprobe
│   │   ├── storage.py       # Gestão de pastas, meta.json e lixeira (trash)
│   │   └── waveform.py      # Geração automática da imagem waveform.png
│   └── templates/
│       └── files.html       # Interface web simples para navegador
├── storage/                 # Diretório raiz dos áudios armazenados
│   ├── 2026/09/16/{UUID}/   # Estrutura por data e UUID
│   │   ├── audio_original.{ext}
│   │   ├── audio_processed.{ext}
│   │   ├── meta.json
│   │   └── waveform.png
│   └── trash/               # Lixeira temporária para arquivos removidos
├── requirements.txt         # Dependências Python do backend
└── run_server.py            # Script executável para inicialização
```

---

## 2. Requisitos e Instalação

### Pré-requisitos
- **Python 3.10+**
- **FFmpeg** e **ffprobe** instalados no sistema (`sudo apt install ffmpeg`)
- **Docker** e **Docker Compose** (para o banco PostgreSQL)

### Instalação das dependências
```bash
# Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instale os pacotes do servidor
pip install -r server/requirements.txt
```

---

## 3. Configuração do Banco de Dados (PostgreSQL)

O banco de dados roda via Docker Compose configurado na porta `5434` (para evitar conflitos com instâncias locais do Postgres):

```bash
# Iniciar o banco PostgreSQL em segundo plano
docker compose up -d

# Verificar se o container está saudável
docker ps --filter "name=audio_postgres"
```

> **Nota:** As tabelas do banco de dados são criadas automaticamente no início da aplicação pelo SQLAlchemy (`init_db()`).

---

## 4. Executando o Servidor

```bash
# Pelo script auxiliar
python server/run_server.py

# Ou diretamente com uvicorn
uvicorn server.app.main:app --host 0.0.0.0 --port 8000 --reload
```

URLs úteis:
- **Interface Web de Arquivos:** [http://localhost:8000/files](http://localhost:8000/files) (ou [http://localhost:8000/](http://localhost:8000/))
- **Documentação Interativa (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentação ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 5. Contrato da API REST (Guia para Integração com o Cliente - Pessoa 1)

### 5.1 Enviar Áudio para Processamento
- **Rota:** `POST /process-audio` (ou `POST /audios/process`)
- **Content-Type:** `multipart/form-data`
- **Campos do Formulário:**
  - `file`: Arquivo de áudio binário (`.mp3`, `.wav`, `.ogg`, `.flac`, `.aac`). *(Obrigatório)*
  - `processing_type`: Operação desejada. *(Obrigatório)* Opções válidas:
    - `"normalize_volume"`: Normalização EBU R128 (loudnorm).
    - `"mono"`: Conversão de stereo para canal único.
    - `"speed"`: Alteração de velocidade (requer `speed_factor`, ex: `0.5`, `1.5`, `2.0`).
    - `"bitrate"`: Redução de bitrate (requer `target_bitrate`, ex: `"64k"`, `"96k"`, `"128k"`).
    - `"format_conversion"`: Conversão de formato (requer `target_format`, ex: `"mp3"`, `"wav"`, `"ogg"`).
  - `speed_factor`: Float (opcional, padrão `1.5`).
  - `target_bitrate`: String (opcional, padrão `"64k"`).
  - `target_format`: String (opcional, ex: `"mp3"`).

- **Exemplo de Resposta (JSON):**
```json
{
  "id": "e67b2d29-1065-4bb6-a831-29472e391b8d",
  "original_name": "musica.mp3",
  "original_ext": ".mp3",
  "mime_type": "audio/mpeg",
  "size_bytes": 5242880,
  "duration_sec": 182.4,
  "sample_rate": 44100,
  "channels": 2,
  "bitrate": 192000,
  "processing_type": "normalize_volume",
  "processing_params": "{\"speed_factor\": 1.5, \"target_bitrate\": \"64k\", \"target_format\": null, \"volume_gain\": null}",
  "created_at": "2026-09-16T22:30:00.000000+00:00",
  "is_deleted": false,
  "urls": {
    "original": "http://localhost:8000/audio/e67b2d29-1065-4bb6-a831-29472e391b8d/original",
    "processed": "http://localhost:8000/audio/e67b2d29-1065-4bb6-a831-29472e391b8d/processed",
    "waveform": "http://localhost:8000/audio/e67b2d29-1065-4bb6-a831-29472e391b8d/waveform",
    "meta": "http://localhost:8000/audio/e67b2d29-1065-4bb6-a831-29472e391b8d/meta",
    "details": "http://localhost:8000/audio/e67b2d29-1065-4bb6-a831-29472e391b8d"
  }
}
```

### 5.2 Consultar Histórico de Áudios
- **Rota:** `GET /audios`
- **Parâmetros Query:**
  - `skip`: inteiro (padrão 0)
  - `limit`: inteiro (padrão 50)
  - `include_deleted`: booleano (padrão false)
- **Resposta:** Lista de objetos `AudioResponse` ordenados pelos mais recentes.

### 5.3 Buscar Detalhes de um Áudio
- **Rota:** `GET /audio/{uuid}` (ou `GET /audios/{id}`)
- **Resposta:** Objeto `AudioResponse` correspondente.

### 5.4 Download e Streaming dos Arquivos
- **Áudio Original:** `GET /audio/{uuid}/original` (Stream direto com Content-Type adequado)
- **Áudio Processado:** `GET /audio/{uuid}/processed` (Stream direto com Content-Type adequado)
- **Forma de Onda (Waveform):** `GET /audio/{uuid}/waveform` (Imagem `image/png`)
- **Metadados JSON:** `GET /audio/{uuid}/meta` (JSON com checksums e detalhes técnicos)

### 5.5 Excluir Áudio (Mover para Lixeira)
- **Rota:** `DELETE /audio/{uuid}`
- **Comportamento:** Move a pasta do áudio para `storage/trash/{UUID}_{timestamp}` e marca `is_deleted = True` no banco de dados.

---

## 6. Testes Automatizados

O projeto possui suíte completa de testes cobrindo FFmpeg, extração de metadados, geração de waveform, endpoints da API e integração com PostgreSQL:

```bash
# Executar todos os testes
pytest tests/ -v

# Executar apenas testes de integração do PostgreSQL
pytest tests/test_postgres_integration.py -v
```

