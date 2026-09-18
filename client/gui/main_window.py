import os
import tempfile

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QComboBox,
    QTextEdit,
    QListWidget,
    QGroupBox,
    QStatusBar,
    QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from audio.metadata import get_audio_metadata
from api.client import (
    send_audio,
    get_history,
    get_audio_details,
    download_original_audio,
    download_processed_audio,
    download_waveform,
    check_server
)
from audio.player import AudioPlayer


class MainWindow(QMainWindow):

    PROCESSING_MAP = {
        "Normalização de volume": "normalize_volume",
        "Converter para mono": "mono",
        "Alterar velocidade": "speed",
        "Reduzir bitrate": "bitrate",
        "Converter formato": "format_conversion"
    }

    def __init__(self):
        super().__init__()

        self.selected_file = None
        self.processed_file = None
        self.waveform_file = None
        self.server_online = False
        self.history_records = []

        self.player = AudioPlayer()

        self.setWindowTitle("Sistema de Processamento de Áudio - Cliente PySide6")
        self.resize(920, 820)

        self.setup_ui()
        self.setup_status_bar()
        self.check_server_status()
        self.load_history()

    # ==================================
    # INTERFACE
    # ==================================

    def setup_ui(self):
        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # TÍTULO
        title = QLabel("🎵 Sistema de Processamento de Áudio")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ARQUIVO
        file_box = QGroupBox("Arquivo selecionado")
        file_layout = QHBoxLayout()

        self.file_label = QLabel("Nenhum arquivo selecionado")
        select_button = QPushButton("📁 Selecionar áudio")
        select_button.clicked.connect(self.select_file)

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_button)
        file_box.setLayout(file_layout)
        layout.addWidget(file_box)

        # INFORMAÇÕES
        info_box = QGroupBox("Informações do áudio")
        info_layout = QVBoxLayout()

        self.audio_info = QTextEdit()
        self.audio_info.setReadOnly(True)
        self.audio_info.setMaximumHeight(130)
        info_layout.addWidget(self.audio_info)
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)

        # FORMA DE ONDA (WAVEFORM)
        waveform_box = QGroupBox("Visualização da Forma de Onda (Waveform)")
        waveform_layout = QVBoxLayout()
        self.waveform_label = QLabel("Nenhuma forma de onda carregada.")
        self.waveform_label.setAlignment(Qt.AlignCenter)
        self.waveform_label.setMinimumHeight(80)
        self.waveform_label.setMaximumHeight(120)
        self.waveform_label.setStyleSheet("background-color: #1a1a24; border-radius: 6px; color: #888899;")
        waveform_layout.addWidget(self.waveform_label)
        waveform_box.setLayout(waveform_layout)
        layout.addWidget(waveform_box)

        # PROCESSAMENTO
        process_box = QGroupBox("Configuração do Processamento")
        process_layout = QVBoxLayout()

        combo_layout = QHBoxLayout()
        self.processing_combo = QComboBox()
        self.processing_combo.addItems([
            "Normalização de volume",
            "Converter para mono",
            "Alterar velocidade",
            "Reduzir bitrate",
            "Converter formato"
        ])
        self.processing_combo.currentTextChanged.connect(self.on_processing_changed)
        combo_layout.addWidget(self.processing_combo)

        # Parâmetro extra dinâmico
        self.extra_param_combo = QComboBox()
        self.extra_param_combo.setVisible(False)
        combo_layout.addWidget(self.extra_param_combo)

        process_layout.addLayout(combo_layout)

        self.send_button = QPushButton("📤 Enviar para processamento no servidor")
        self.send_button.clicked.connect(self.send_audio)
        process_layout.addWidget(self.send_button)

        process_box.setLayout(process_layout)
        layout.addWidget(process_box)

        # REPRODUÇÃO
        audio_box = QGroupBox("Reprodução de Áudio")
        audio_layout = QHBoxLayout()

        self.play_button = QPushButton("▶ Áudio Original")
        self.play_button.clicked.connect(self.play_audio)

        self.play_processed_button = QPushButton("✨ Áudio Processado")
        self.play_processed_button.clicked.connect(self.play_processed_audio)
        self.play_processed_button.setEnabled(False)

        self.stop_button = QPushButton("■ Parar Reprodução")
        self.stop_button.clicked.connect(self.stop_audio)

        audio_layout.addWidget(self.play_button)
        audio_layout.addWidget(self.play_processed_button)
        audio_layout.addWidget(self.stop_button)

        audio_box.setLayout(audio_layout)
        layout.addWidget(audio_box)

        # HISTÓRICO
        history_box = QGroupBox("Histórico de processamentos (Clique em um item para inspecionar/reproduzir)")
        history_layout = QVBoxLayout()

        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(140)
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        history_layout.addWidget(self.history_list)

        btn_refresh = QPushButton("🔄 Atualizar Histórico")
        btn_refresh.clicked.connect(self.load_history)
        history_layout.addWidget(btn_refresh)

        history_box.setLayout(history_layout)
        layout.addWidget(history_box)

        container.setLayout(layout)
        self.setCentralWidget(container)
        self.apply_style()

    # ==================================
    # CONTROLE DE PARÂMETROS
    # ==================================

    def on_processing_changed(self, text):
        if text == "Alterar velocidade":
            self.extra_param_combo.clear()
            self.extra_param_combo.addItems(["0.5x (Lento)", "0.75x", "1.25x", "1.5x (Rápido)", "2.0x (Dobro)"])
            self.extra_param_combo.setCurrentText("1.5x (Rápido)")
            self.extra_param_combo.setVisible(True)
        elif text == "Reduzir bitrate":
            self.extra_param_combo.clear()
            self.extra_param_combo.addItems(["64 kbps (Econômico)", "96 kbps", "128 kbps"])
            self.extra_param_combo.setCurrentText("64 kbps (Econômico)")
            self.extra_param_combo.setVisible(True)
        elif text == "Converter formato":
            self.extra_param_combo.clear()
            self.extra_param_combo.addItems(["MP3", "WAV", "OGG", "FLAC"])
            self.extra_param_combo.setCurrentText("MP3")
            self.extra_param_combo.setVisible(True)
        else:
            self.extra_param_combo.setVisible(False)

    # ==================================
    # STATUS BAR
    # ==================================

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Pronto")

    def check_server_status(self):
        self.server_online = check_server()
        self.update_status("Pronto")

    def update_status(self, status):
        filename = "Nenhum"
        if self.selected_file:
            filename = os.path.basename(self.selected_file)
            if len(filename) > 30:
                filename = filename[:27] + "..."

        server_status = "Online" if self.server_online else "Offline"
        self.status_bar.showMessage(
            f"Servidor: {server_status} | Arquivo: {filename} | Status: {status}"
        )

    def format_duration(self, seconds):
        if seconds is None:
            return "Desconhecida"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    # ==================================
    # SELEÇÃO DO ÁUDIO
    # ==================================

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo de áudio",
            "",
            "Áudios (*.mp3 *.wav *.ogg *.flac *.aac *.m4a)"
        )

        if not file_path:
            return

        self.selected_file = file_path
        self.processed_file = None
        self.play_processed_button.setEnabled(False)
        self.waveform_label.setText("Envie o áudio para gerar a forma de onda.")
        self.waveform_label.setPixmap(QPixmap())

        filename = os.path.basename(file_path)
        display_name = filename if len(filename) <= 35 else filename[:32] + "..."
        self.file_label.setText(display_name)
        self.update_status("Arquivo selecionado")

        metadata = get_audio_metadata(file_path)
        if "error" in metadata:
            self.audio_info.setText(metadata["error"])
            return

        duration_formatted = self.format_duration(metadata.get("duration"))
        size_kb = metadata.get("size_bytes", 0) / 1024
        info = (
            f"Arquivo: {metadata.get('name')}\n"
            f"Formato: {metadata.get('extension')}\n"
            f"Tamanho: {size_kb:.2f} KB\n"
            f"Duração: {duration_formatted}\n"
            f"Taxa de Amostragem: {metadata.get('sample_rate')} Hz\n"
            f"Canais: {metadata.get('channels')}"
        )
        self.audio_info.setText(info)

    # ==================================
    # REPRODUÇÃO
    # ==================================

    def play_audio(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Aviso", "Selecione ou baixe um áudio primeiro.")
            return
        self.player.play(self.selected_file)
        self.update_status("Reproduzindo áudio original")

    def stop_audio(self):
        self.player.stop()
        self.update_status("Áudio parado")

    def play_processed_audio(self):
        if not self.processed_file or not os.path.exists(self.processed_file):
            QMessageBox.warning(self, "Aviso", "Nenhum áudio processado disponível.")
            return
        self.player.play(self.processed_file)
        self.update_status("Reproduzindo áudio processado")

    # ==================================
    # ENVIO PARA O SERVIDOR
    # ==================================

    def send_audio(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo primeiro.")
            return

        self.check_server_status()
        if not self.server_online:
            QMessageBox.critical(self, "Servidor indisponível", "Não foi possível conectar ao servidor.")
            return

        self.update_status("Enviando áudio...")
        self.send_button.setEnabled(False)

        processing = self.processing_combo.currentText()
        processing_type = self.PROCESSING_MAP[processing]

        extra_kwargs = {}
        if processing_type == "speed":
            text = self.extra_param_combo.currentText()
            speed_val = text.split("x")[0].strip()
            extra_kwargs["speed_factor"] = speed_val
        elif processing_type == "bitrate":
            text = self.extra_param_combo.currentText()
            bitrate_val = text.split()[0] + "k"
            extra_kwargs["target_bitrate"] = bitrate_val
        elif processing_type == "format_conversion":
            extra_kwargs["target_format"] = self.extra_param_combo.currentText().lower()

        try:
            response = send_audio(self.selected_file, processing_type, **extra_kwargs)

            if "error" in response:
                self.audio_info.append(f"\n❌ Erro no processamento:\n{response['error']}")
                self.update_status("Erro")
                return

            audio_id = response.get("id")
            urls = response.get("urls", {})
            processed_url = urls.get("processed")
            waveform_url = urls.get("waveform")

            self.audio_info.append(
                f"\n✅ Processamento concluído com sucesso!\n"
                f"ID: {audio_id} | Tipo: {processing}"
            )

            temp_dir = os.path.join(tempfile.gettempdir(), "audio_processing_client")
            os.makedirs(temp_dir, exist_ok=True)

            # Download do processado
            if processed_url:
                ext = response.get("original_ext", ".mp3")
                if processing_type == "format_conversion" and "target_format" in extra_kwargs:
                    ext = f".{extra_kwargs['target_format']}"
                processed_path = os.path.join(temp_dir, f"{audio_id}_processed{ext}")

                self.update_status("Baixando áudio processado...")
                dl_res = download_processed_audio(processed_url, processed_path)
                if dl_res.get("success"):
                    self.processed_file = dl_res["path"]
                    self.play_processed_button.setEnabled(True)
                    self.audio_info.append("🎧 Áudio processado pronto para reprodução.")

            # Download da Waveform
            if waveform_url:
                wave_path = os.path.join(temp_dir, f"{audio_id}_waveform.png")
                w_res = download_waveform(waveform_url, wave_path)
                if w_res.get("success") and os.path.exists(wave_path):
                    self.waveform_file = wave_path
                    pixmap = QPixmap(wave_path)
                    if not pixmap.isNull():
                        self.waveform_label.setPixmap(
                            pixmap.scaled(self.waveform_label.width() or 800, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        )

            self.load_history()
            self.update_status("Finalizado com sucesso")

        except Exception as e:
            self.audio_info.append(f"\n❌ Erro inesperado:\n{e}")
            self.update_status("Erro")
        finally:
            self.send_button.setEnabled(True)

    # ==================================
    # HISTÓRICO
    # ==================================

    def load_history(self):
        self.history_list.clear()
        self.history_records = []
        history = get_history()

        if isinstance(history, dict) and "error" in history:
            self.history_list.addItem("Servidor indisponível.")
            return

        if not isinstance(history, list) or len(history) == 0:
            self.history_list.addItem("Nenhum processamento realizado.")
            return

        self.history_records = history
        for audio in history:
            name = audio.get("original_name", "Arquivo")
            processing = audio.get("processing_type", "-")
            audio_id = audio.get("id", "-")
            dur = audio.get("duration_sec")
            dur_str = f"{dur:.1f}s" if dur else ""
            item_text = f"🎵 {name} | {processing} | {dur_str} | ID: {audio_id[:8]}..."
            self.history_list.addItem(item_text)

    def on_history_item_clicked(self, item):
        row = self.history_list.row(item)
        if row < 0 or row >= len(self.history_records):
            return

        audio_data = self.history_records[row]
        audio_id = audio_data.get("id")
        if not audio_id:
            return

        self.update_status(f"Carregando áudio do histórico: {audio_id[:8]}...")

        # Exibe informações na tela
        dur = audio_data.get("duration_sec")
        info = (
            f"--- Item do Histórico ---\n"
            f"Arquivo: {audio_data.get('original_name')}\n"
            f"ID: {audio_id}\n"
            f"Processamento: {audio_data.get('processing_type')}\n"
            f"Duração: {self.format_duration(dur)}\n"
            f"Sample Rate: {audio_data.get('sample_rate')} Hz\n"
            f"Canais: {audio_data.get('channels')}\n"
            f"Tamanho: {(audio_data.get('size_bytes', 0) / 1024):.2f} KB"
        )
        self.audio_info.setText(info)

        temp_dir = os.path.join(tempfile.gettempdir(), "audio_processing_client")
        os.makedirs(temp_dir, exist_ok=True)

        urls = audio_data.get("urls", {})

        # Baixa waveform do histórico
        wave_url = urls.get("waveform") or f"/audio/{audio_id}/waveform"
        wave_path = os.path.join(temp_dir, f"{audio_id}_waveform.png")
        w_res = download_waveform(wave_url, wave_path)
        if w_res.get("success") and os.path.exists(wave_path):
            pixmap = QPixmap(wave_path)
            if not pixmap.isNull():
                self.waveform_label.setPixmap(
                    pixmap.scaled(self.waveform_label.width() or 800, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        # Baixa processado para reproduzir
        proc_url = urls.get("processed") or f"/audio/{audio_id}/processed"
        proc_path = os.path.join(temp_dir, f"{audio_id}_processed{audio_data.get('original_ext', '.mp3')}")
        p_res = download_processed_audio(proc_url, proc_path)
        if p_res.get("success"):
            self.processed_file = p_res["path"]
            self.play_processed_button.setEnabled(True)

        # Baixa original para reproduzir
        orig_url = urls.get("original") or f"/audio/{audio_id}/original"
        orig_path = os.path.join(temp_dir, f"{audio_id}_original{audio_data.get('original_ext', '.mp3')}")
        o_res = download_original_audio(orig_url, orig_path)
        if o_res.get("success"):
            self.selected_file = o_res["path"]
            self.file_label.setText(audio_data.get("original_name"))

        self.update_status("Áudio do histórico carregado para reprodução")

    # ==================================
    # ESTILO
    # ==================================

    def apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                color: #f8fafc;
                font-size: 13px;
            }
            QLabel#title {
                font-size: 19px;
                font-weight: bold;
                color: #38bdf8;
                padding: 6px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 8px;
                padding: 10px;
                background-color: #1e293b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #94a3b8;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 8px 14px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
            QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                color: #f8fafc;
                padding: 6px 10px;
                border-radius: 6px;
            }
            QTextEdit, QListWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #e2e8f0;
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
                color: white;
            }
            QStatusBar {
                background-color: #090d16;
                color: #94a3b8;
                font-size: 12px;
            }
        """)