# Cliente Desktop - Processamento de Áudio (PySide6)

Aplicação cliente desenvolvida em **Python** com **PySide6 (Qt)** para interação do usuário, seleção de áudios, leitura local de metadados, envio para a API REST do servidor, exibição da forma de onda (*waveform*) e reprodução de áudio original e processado.

---

## 1. Estrutura do Cliente

```text
client/
├── main.py              # Ponto de entrada da aplicação gráfica
├── api/
│   ├── __init__.py
│   └── client.py        # Módulo de comunicação HTTP (requests) com a API
├── audio/
│   ├── __init__.py
│   ├── metadata.py      # Extração local de metadados (Mutagen)
│   └── player.py        # Reprodução de áudio (Pygame / Qt)
├── config/
│   ├── __init__.py
│   └── settings.py      # Configuração de IP/porta do servidor
├── gui/
│   ├── __init__.py
│   └── main_window.py   # Janela principal e componentes visuais
├── tests/
│   ├── audios/          # Amostras de teste em formato .mp3
│   └── test_client.py   # Testes unitários do cliente
└── requirements.txt     # Dependências do cliente
```

---

## 2. Instalação de Dependências

Certifique-se de ter o Python 3.10+ instalado.

```bash
# Crie e ative o ambiente virtual (caso ainda não tenha criado)
python3 -m venv .venv
source .venv/bin/activate

# Instale os pacotes do cliente
pip install -r client/requirements.txt
```

---

## 3. Configuração do Endereço do Servidor

Por padrão, o cliente se conecta ao servidor em `127.0.0.1:8000`.

Para conectar a um servidor rodando em outra máquina na rede local:
```bash
# Definindo variáveis de ambiente antes de executar:
export SERVER_HOST="192.168.1.100"
export SERVER_PORT=8000

# Ou definindo a URL completa diretamente:
export API_URL="http://192.168.1.100:8000"
```

Alternativamente, você pode editar o arquivo `client/config/settings.py`.

---

## 4. Como Executar a Aplicação

Com o servidor rodando e o ambiente virtual ativado:

```bash
python client/main.py
```

---

## 5. Funcionalidades da Interface

1. **Seleção de Arquivo e Leitura de Metadados:**
   - Permite escolher arquivos `.mp3`, `.wav`, `.ogg`, `.flac`, `.aac`.
   - Lê instantaneamente duração, tamanho em KB, taxa de amostragem (Hz), canais e extensão usando a biblioteca `mutagen`.
2. **Configuração de Processamento:**
   - **Normalização de volume**: Ajuste de loudness para padrão EBU R128.
   - **Converter para mono**: Downmixing para canal único.
   - **Alterar velocidade**: Ajustes dinâmicos entre 0.5x e 2.0x.
   - **Reduzir bitrate**: Taxas econômicas (64 kbps, 96 kbps, 128 kbps).
   - **Converter formato**: Conversão para MP3, WAV, OGG ou FLAC.
3. **Reprodução Dual:**
   - Botão **▶ Áudio Original**: Reproduz o arquivo selecionado localmente ou baixado do histórico.
   - Botão **✨ Áudio Processado**: Reproduz o resultado gerado pelo FFmpeg no servidor.
   - Botão **■ Parar Reprodução**: Interrompe qualquer áudio em execução.
4. **Forma de Onda (Waveform):**
   - Baixa e renderiza automaticamente a imagem `waveform.png` gerada pelo servidor com alta resolução.
5. **Histórico Interativo:**
   - Lista todos os áudios processados no servidor.
   - Ao clicar em qualquer item do histórico, o cliente baixa o áudio original, o processado e a waveform, habilitando a reprodução imediata.

---

## 6. Testes Automatizados do Cliente

```bash
pytest client/tests/ -v
```

