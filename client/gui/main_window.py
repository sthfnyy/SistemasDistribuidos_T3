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

from audio.metadata import get_audio_metadata

from api.client import (
    send_audio,
    get_history,
    download_processed_audio,
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

        self.server_online = False

        self.player = AudioPlayer()

        self.setWindowTitle(
            "Sistema de Processamento de Áudio"
        )

        self.resize(
            900,
            750
        )

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

        layout.setSpacing(12)


        # ==============================
        # TÍTULO
        # ==============================

        title = QLabel(
            "🎵 Sistema de Processamento de Áudio"
        )

        title.setObjectName(
            "title"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            title
        )


        # ==============================
        # ARQUIVO
        # ==============================

        file_box = QGroupBox(
            "Arquivo selecionado"
        )

        file_layout = QHBoxLayout()

        self.file_label = QLabel(
            "Nenhum arquivo selecionado"
        )

        select_button = QPushButton(
            "Selecionar áudio"
        )

        select_button.clicked.connect(
            self.select_file
        )

        file_layout.addWidget(
            self.file_label
        )

        file_layout.addWidget(
            select_button
        )

        file_box.setLayout(
            file_layout
        )

        layout.addWidget(
            file_box
        )


        # ==============================
        # INFORMAÇÕES
        # ==============================

        info_box = QGroupBox(
            "Informações do áudio"
        )

        info_layout = QVBoxLayout()

        self.audio_info = QTextEdit()

        self.audio_info.setReadOnly(
            True
        )

        self.audio_info.setMaximumHeight(
            180
        )

        info_layout.addWidget(
            self.audio_info
        )

        info_box.setLayout(
            info_layout
        )

        layout.addWidget(
            info_box
        )


        # ==============================
        # REPRODUÇÃO
        # ==============================

        audio_box = QGroupBox(
            "Reprodução"
        )

        audio_layout = QVBoxLayout()


        # ORIGINAL

        original_layout = QHBoxLayout()

        original_label = QLabel(
            "Áudio original"
        )

        self.play_button = QPushButton(
            "▶ Reproduzir"
        )

        self.play_button.clicked.connect(
            self.play_audio
        )

        self.stop_button = QPushButton(
            "■ Parar"
        )

        self.stop_button.clicked.connect(
            self.stop_audio
        )

        original_layout.addWidget(
            original_label
        )

        original_layout.addWidget(
            self.play_button
        )

        original_layout.addWidget(
            self.stop_button
        )


        # PROCESSADO

        processed_layout = QHBoxLayout()

        processed_label = QLabel(
            "Áudio processado"
        )

        self.play_processed_button = QPushButton(
            "▶ Reproduzir processado"
        )

        self.play_processed_button.clicked.connect(
            self.play_processed_audio
        )

        self.play_processed_button.setEnabled(
            False
        )

        processed_layout.addWidget(
            processed_label
        )

        processed_layout.addWidget(
            self.play_processed_button
        )


        audio_layout.addLayout(
            original_layout
        )

        audio_layout.addLayout(
            processed_layout
        )

        audio_box.setLayout(
            audio_layout
        )

        layout.addWidget(
            audio_box
        )


        # ==============================
        # PROCESSAMENTO
        # ==============================

        process_box = QGroupBox(
            "Processamento"
        )

        process_layout = QVBoxLayout()

        self.processing_combo = QComboBox()

        self.processing_combo.addItems(
            [
                "Normalização de volume",
                "Converter para mono",
                "Alterar velocidade",
                "Reduzir bitrate",
                "Converter formato"
            ]
        )

        process_layout.addWidget(
            self.processing_combo
        )


        self.send_button = QPushButton(
            "📤 Enviar para servidor"
        )

        self.send_button.clicked.connect(
            self.send_audio
        )

        process_layout.addWidget(
            self.send_button
        )

        process_box.setLayout(
            process_layout
        )

        layout.addWidget(
            process_box
        )


        # ==============================
        # HISTÓRICO
        # ==============================

        history_box = QGroupBox(
            "Histórico de processamentos"
        )

        history_layout = QVBoxLayout()

        self.history_list = QListWidget()

        self.history_list.setMaximumHeight(
            150
        )

        history_layout.addWidget(
            self.history_list
        )

        history_box.setLayout(
            history_layout
        )

        layout.addWidget(
            history_box
        )


        container.setLayout(
            layout
        )

        self.setCentralWidget(
            container
        )

        self.apply_style()


    # ==================================
    # STATUS BAR
    # ==================================

    def setup_status_bar(self):

        self.status_bar = QStatusBar()

        self.setStatusBar(
            self.status_bar
        )

        self.update_status(
            "Pronto"
        )


    def check_server_status(self):

        self.server_online = check_server()

        self.update_status(
            "Pronto"
        )


    def update_status(
        self,
        status
    ):

        filename = "Nenhum"

        if self.selected_file:

            filename = os.path.basename(
                self.selected_file
            )

            if len(filename) > 35:

                filename = (
                    filename[:32]
                    + "..."
                )


        server_status = (
            "Online"
            if self.server_online
            else "Offline"
        )


        self.status_bar.showMessage(
            f"Servidor: {server_status} | "
            f"Arquivo: {filename} | "
            f"Status: {status}"
        )


    # ==================================
    # UTILIDADES
    # ==================================

    def format_duration(
        self,
        seconds
    ):

        if seconds is None:

            return "Desconhecida"

        minutes = int(
            seconds // 60
        )

        seconds = int(
            seconds % 60
        )

        return (
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )


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

        # Ao selecionar outro arquivo,
        # o processado anterior deixa de ser válido.
        self.processed_file = None

        self.play_processed_button.setEnabled(
            False
        )


        filename = os.path.basename(
            file_path
        )


        display_name = filename

        if len(display_name) > 35:

            display_name = (
                display_name[:32]
                + "..."
            )


        self.file_label.setText(
            display_name
        )


        self.update_status(
            "Arquivo selecionado"
        )


        metadata = get_audio_metadata(
            file_path
        )


        if "error" in metadata:

            self.audio_info.setText(
                metadata["error"]
            )

            return


        info = (
            f"Nome: {metadata['name']}\n\n"
            f"Formato: {metadata['extension']}\n\n"
            f"Tamanho: "
            f"{metadata['size_bytes'] / 1024:.2f} KB\n\n"
            f"Duração: "
            f"{self.format_duration(metadata['duration'])}\n\n"
            f"Sample Rate: "
            f"{metadata['sample_rate']} Hz\n\n"
            f"Canais: "
            f"{metadata['channels']}"
        )


        self.audio_info.setText(
            info
        )


    # ==================================
    # REPRODUÇÃO
    # ==================================

    def play_audio(self):

        if not self.selected_file:

            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione um áudio primeiro."
            )

            return


        self.player.play(
            self.selected_file
        )


        self.update_status(
            "Reproduzindo áudio original"
        )


    def stop_audio(self):

        self.player.stop()


        self.update_status(
            "Áudio parado"
        )


    def play_processed_audio(self):

        if not self.processed_file:

            QMessageBox.warning(
                self,
                "Aviso",
                "Nenhum áudio processado disponível."
            )

            return


        if not os.path.exists(
            self.processed_file
        ):

            QMessageBox.warning(
                self,
                "Aviso",
                "O arquivo processado não foi encontrado."
            )

            return


        self.player.play(
            self.processed_file
        )


        self.update_status(
            "Reproduzindo áudio processado"
        )


    # ==================================
    # ENVIO PARA O SERVIDOR
    # ==================================

    def send_audio(self):

        if not self.selected_file:

            QMessageBox.warning(
                self,
                "Aviso",
                "Selecione um arquivo primeiro."
            )

            return


        self.check_server_status()


        if not self.server_online:

            QMessageBox.critical(
                self,
                "Servidor indisponível",
                "Não foi possível conectar ao servidor."
            )

            return


        self.update_status(
            "Enviando áudio..."
        )


        self.send_button.setEnabled(
            False
        )


        processing = (
            self.processing_combo.currentText()
        )


        processing_type = (
            self.PROCESSING_MAP[processing]
        )


        try:

            response = send_audio(
                self.selected_file,
                processing_type
            )


            # ==========================
            # ERRO
            # ==========================

            if "error" in response:

                self.audio_info.append(
                    "\n\n❌ Erro no processamento:\n"
                    + response["error"]
                )

                self.update_status(
                    "Erro"
                )

                return


            # ==========================
            # RESPOSTA DO SERVIDOR
            # ==========================

            audio_id = response.get(
                "id"
            )


            urls = response.get(
                "urls",
                {}
            )


            processed_url = urls.get(
                "processed"
            )


            self.audio_info.append(
                "\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ Processamento concluído!\n\n"
                f"Processamento: {processing}\n"
                f"ID: {audio_id}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )


            # ==========================
            # DOWNLOAD DO PROCESSADO
            # ==========================

            if processed_url:

                original_extension = os.path.splitext(
                    self.selected_file
                )[1]

                if not original_extension:

                    original_extension = ".mp3"


                temp_directory = os.path.join(
                    tempfile.gettempdir(),
                    "audio_processing_client"
                )


                os.makedirs(
                    temp_directory,
                    exist_ok=True
                )


                processed_path = os.path.join(
                    temp_directory,
                    f"{audio_id}_processed"
                    f"{original_extension}"
                )


                self.update_status(
                    "Baixando áudio processado..."
                )


                download_result = (
                    download_processed_audio(
                        processed_url,
                        processed_path
                    )
                )


                if download_result.get(
                    "success"
                ):

                    self.processed_file = (
                        download_result["path"]
                    )


                    self.play_processed_button.setEnabled(
                        True
                    )


                    self.audio_info.append(
                        "\n🎧 Áudio processado "
                        "pronto para reprodução."
                    )


                else:

                    self.processed_file = None

                    self.play_processed_button.setEnabled(
                        False
                    )


                    self.audio_info.append(
                        "\n⚠ Processamento concluído, "
                        "mas não foi possível baixar "
                        "o áudio processado.\n"
                        f"{download_result.get('error')}"
                    )


            else:

                self.audio_info.append(
                    "\n⚠ O servidor não retornou "
                    "a URL do áudio processado."
                )


            # Atualiza histórico

            self.load_history()


            self.update_status(
                "Finalizado"
            )


        except Exception as e:

            self.audio_info.append(
                f"\n\n❌ Erro inesperado:\n{e}"
            )


            self.update_status(
                "Erro"
            )


        finally:

            self.send_button.setEnabled(
                True
            )


    # ==================================
    # HISTÓRICO
    # ==================================

    def load_history(self):

        self.history_list.clear()


        history = get_history()


        if isinstance(
            history,
            dict
        ):

            if "error" in history:

                self.history_list.addItem(
                    "Servidor indisponível."
                )

                return


            if "detail" in history:

                self.history_list.addItem(
                    str(history["detail"])
                )

                return


        if not isinstance(
            history,
            list
        ):

            self.history_list.addItem(
                "Histórico indisponível."
            )

            return


        if len(history) == 0:

            self.history_list.addItem(
                "Nenhum processamento realizado."
            )

            return


        for audio in history:

            name = audio.get(
                "original_name",
                "Arquivo desconhecido"
            )


            processing = audio.get(
                "processing_type",
                "-"
            )


            audio_id = audio.get(
                "id",
                "-"
            )


            processing_names = {

                "normalize_volume":
                    "Normalização de volume",

                "normalize":
                    "Normalização de volume",

                "mono":
                    "Conversão para mono",

                "speed":
                    "Alteração de velocidade",

                "bitrate":
                    "Redução de bitrate",

                "format_conversion":
                    "Conversão de formato",

                "convert":
                    "Conversão de formato"
            }


            processing_display = (
                processing_names.get(
                    processing,
                    processing
                )
            )


            item = (
                f"🎵 {name}  |  "
                f"{processing_display}  |  "
                f"ID: {audio_id}"
            )


            self.history_list.addItem(
                item
            )


    # ==================================
    # ESTILO
    # ==================================

    def apply_style(self):

        self.setStyleSheet(
            """

            QWidget {

                font-size: 14px;

            }


            QLabel#title {

                font-size: 20px;

                font-weight: bold;

                padding: 8px;

            }


            QGroupBox {

                font-weight: bold;

                border: 1px solid #cccccc;

                border-radius: 8px;

                margin-top: 10px;

                padding: 10px;

            }


            QGroupBox::title {

                subcontrol-origin: margin;

                left: 10px;

                padding: 0 5px;

            }


            QPushButton {

                padding: 8px;

                border-radius: 6px;

            }


            QPushButton:hover {

                background-color: #444444;

            }


            QPushButton:disabled {

                color: #777777;

            }


            QComboBox {

                padding: 7px;

                border-radius: 5px;

            }


            QTextEdit {

                border-radius: 6px;

                padding: 5px;

            }


            QListWidget {

                border-radius: 6px;

                padding: 5px;

            }


            QStatusBar {

                font-size: 13px;

            }

            """
        )