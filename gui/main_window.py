# gui/main_window.py

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
                           QProgressBar, QFileDialog, QGroupBox, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
import os
import sys
import humanize
import threading
from pathlib import Path

from core.processor import SubtitleProcessor
from core.model_info import ModelInfo

class SubtitleGUI(QMainWindow):
    # Define custom signals
    progress_signal = pyqtSignal(str, int)  # per status e valore
    error_signal = pyqtSignal(str)          # per messaggi di errore
    success_signal = pyqtSignal(str)        # per messaggi di successo
    update_ui_signal = pyqtSignal()         # per aggiornamenti generici dell'UI

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Creator & Burner")
        self.setMinimumSize(800, 600)

        # Connect the signals
        self.progress_signal.connect(self._update_progress)
        self.error_signal.connect(self._show_error)
        self.success_signal.connect(self._show_success)
        self.update_ui_signal.connect(self._update_ui)

        # Initialize the processor
        self.processor = SubtitleProcessor()

        # Setup UI
        self.init_ui()

        # Load settings
        self.load_saved_settings()

    def _update_progress(self, status: str, value: int):
        """Update the UI in a thread-safe manner."""
        self.status_label.setText(status)
        self.progress_bar.setValue(value)

    def _show_error(self, message: str):
        """Show errors in a thread-safe manner."""
        QMessageBox.critical(self, "Error", message)

    def _show_success(self, message: str):
        """Show success messages in a thread-safe manner."""
        QMessageBox.information(self, "Success", message)

    def _update_ui(self):
        """Update UI elements in a thread-safe manner."""
        self.update_model_status()

    def init_ui(self):
        """Initialize the user interface."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Create UI sections
        main_layout.addWidget(self.create_file_section())
        main_layout.addWidget(self.create_model_section())
        main_layout.addWidget(self.create_font_section())
        main_layout.addWidget(self.create_translation_section())
        main_layout.addWidget(self.create_video_section())
        main_layout.addWidget(self.create_control_section())
        main_layout.addWidget(self.create_progress_section())

    def create_file_section(self) -> QGroupBox:
        """Create the section for file selection."""
        group = QGroupBox("File Selection")
        layout = QGridLayout()

        # Video selection
        self.video_path = QLineEdit()
        video_browse = QPushButton("Browse")
        video_browse.clicked.connect(self.select_video)
        layout.addWidget(QLabel("Video:"), 0, 0)
        layout.addWidget(self.video_path, 0, 1)
        layout.addWidget(video_browse, 0, 2)

        # SRT selection
        self.srt_path = QLineEdit()
        srt_browse = QPushButton("Browse")
        srt_browse.clicked.connect(self.select_srt)
        layout.addWidget(QLabel("SRT:"), 1, 0)
        layout.addWidget(self.srt_path, 1, 1)
        layout.addWidget(srt_browse, 1, 2)

        group.setLayout(layout)
        return group

    def create_model_section(self) -> QGroupBox:
        """Create the Whisper template settings section."""
        group = QGroupBox("Whisper Model Settings")
        layout = QGridLayout()

        # Model selection
        self.model_combo = QComboBox()
        models = list(ModelInfo.SIZES.keys())
        model_infos = [ModelInfo.get_model_info(m) for m in models]
        self.model_combo.addItems(model_infos)
        self.model_combo.currentIndexChanged.connect(lambda: self.update_ui_signal.emit())

        # Model status and download
        self.model_status = QLabel("Not downloaded")
        self.download_button = QPushButton("Download Model")
        self.download_button.clicked.connect(self.download_model)

        layout.addWidget(QLabel("Model:"), 0, 0)
        layout.addWidget(self.model_combo, 0, 1)
        layout.addWidget(self.model_status, 0, 2)
        layout.addWidget(self.download_button, 0, 3)

        # Language selection
        self.language_combo = QComboBox()
        languages = [(code, name) for code, name in ModelInfo.LANGUAGES.items()]
        self.language_combo.addItems([f"{code} - {name}" for code, name in languages])
        layout.addWidget(QLabel("Language:"), 1, 0)
        layout.addWidget(self.language_combo, 1, 1)

        # Progress bar
        self.download_progress = QProgressBar()
        layout.addWidget(self.download_progress, 2, 0, 1, 4)

        group.setLayout(layout)
        return group

    def create_font_section(self) -> QGroupBox:
        """Create the section for font settings."""
        group = QGroupBox("Font Settings")
        layout = QGridLayout()

        # Font size
        self.font_size = QComboBox()
        self.font_size.addItems(["16", "20", "24", "28", "32", "36", "40", "48"])
        layout.addWidget(QLabel("Size:"), 0, 0)
        layout.addWidget(self.font_size, 0, 1)

        # Font family
        self.font_name = QComboBox()
        self.font_name.addItems(["Arial", "Times New Roman", "Helvetica", "Courier"])
        layout.addWidget(QLabel("Font:"), 0, 2)
        layout.addWidget(self.font_name, 0, 3)

        # Font color
        self.font_color = QComboBox()
        self.font_color.addItems(["white", "yellow", "green", "cyan"])
        layout.addWidget(QLabel("Color:"), 1, 0)
        layout.addWidget(self.font_color, 1, 1)

        # Outline color
        self.font_outline = QComboBox()
        self.font_outline.addItems(["black", "white", "none"])
        layout.addWidget(QLabel("Outline:"), 1, 2)
        layout.addWidget(self.font_outline, 1, 3)

        group.setLayout(layout)
        return group

    def create_translation_section(self) -> QGroupBox:
        """Create the translation section."""
        group = QGroupBox("Translation")
        layout = QGridLayout()

        # From language
        self.trans_from = QComboBox()
        self.trans_from.addItems(self.processor.translator.get_supported_languages())
        layout.addWidget(QLabel("From:"), 0, 0)
        layout.addWidget(self.trans_from, 0, 1)

        # To language
        self.trans_to = QComboBox()
        self.trans_to.addItems(self.processor.translator.get_supported_languages())
        layout.addWidget(QLabel("To:"), 0, 2)
        layout.addWidget(self.trans_to, 0, 3)

        # Translate button
        translate_button = QPushButton("Translate SRT")
        translate_button.clicked.connect(self.translate_srt)
        layout.addWidget(translate_button, 1, 0, 1, 4)

        group.setLayout(layout)
        return group

    def create_video_section(self) -> QGroupBox:
        """Create the section for video settings."""
        group = QGroupBox("Video Settings")
        layout = QGridLayout()

        # Quality (CRF)
        self.video_quality = QComboBox()
        self.video_quality.addItems(["18", "23", "28"])
        layout.addWidget(QLabel("Quality:"), 0, 0)
        layout.addWidget(self.video_quality, 0, 1)

        # Encoding preset
        self.video_preset = QComboBox()
        self.video_preset.addItems(["ultrafast", "superfast", "veryfast", "faster",
                                  "fast", "medium", "slow"])
        layout.addWidget(QLabel("Preset:"), 0, 2)
        layout.addWidget(self.video_preset, 0, 3)

        group.setLayout(layout)
        return group

    def create_control_section(self) -> QWidget:
        """Create the controls section."""
        widget = QWidget()
        layout = QHBoxLayout()

        self.process_button = QPushButton("Start Processing")
        self.process_button.clicked.connect(self.start_processing)
        layout.addWidget(self.process_button)

        widget.setLayout(layout)
        return widget

    def create_progress_section(self) -> QGroupBox:
        """Create the section for the progress bar."""
        group = QGroupBox("Progress")
        layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready")

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        group.setLayout(layout)
        return group

    def select_video(self):
        """Manages video file selection."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v)")
        if filename:
            self.video_path.setText(filename)
            if not self.srt_path.text():
                srt_path = str(Path(filename).with_suffix('.srt'))
                self.srt_path.setText(srt_path)

    def select_srt(self):
        """Manages SRT file selection."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle File", "",
            "Subtitle files (*.srt *.ass *.ssa)")
        if filename:
            self.srt_path.setText(filename)

    def update_model_status(self):
        """Update the status of the selected model."""
        selected = self.model_combo.currentText().split()[0]
        if self.processor.is_model_downloaded(selected):
            self.model_status.setText("Downloaded")
            self.download_button.setEnabled(False)
        else:
            size = humanize.naturalsize(ModelInfo.SIZES[selected]['size'])
            self.model_status.setText(f"Not downloaded ({size})")
            self.download_button.setEnabled(True)

    def download_model(self):
        """Manages the download of the selected model."""
        selected = self.model_combo.currentText().split()[0]

        def do_download():
            try:
                self.progress_signal.emit(f"Downloading {selected} model...", 10)
                self.processor.download_model(selected)
                self.progress_signal.emit(f"Model {selected} downloaded successfully!", 100)
                self.update_ui_signal.emit()  # Update model state in a thread-safe manner
            except Exception as e:
                self.error_signal.emit(str(e))
                self.progress_signal.emit("Error downloading model", 0)
            finally:
                # Re-enable buttons in main thread
                self.download_button.setEnabled(True)
                self.process_button.setEnabled(True)

        self.download_button.setEnabled(False)
        self.process_button.setEnabled(False)
        self.progress_bar.setMaximum(100)
        self.progress_signal.emit("Starting download...", 0)
        threading.Thread(target=do_download, daemon=True).start()

    def translate_srt(self):
        """Manages subtitle translation."""
        if not self.srt_path.text():
            self.error_signal.emit("No SRT file selected")
            return

        def do_translate():
            try:
                self.progress_signal.emit("Translating subtitles...", 50)
                output_file = self.processor.translate_subtitles(
                    self.srt_path.text(),
                    self.trans_from.currentText(),
                    self.trans_to.currentText()
                )

                self.progress_signal.emit("Translation completed!", 100)

                # Ask the user if he wants to use the translated file
                reply = QMessageBox.question(
                    self, "Success",
                    f"Translation completed!\nUse translated file?\n{output_file}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.srt_path.setText(output_file)

            except Exception as e:
                self.error_signal.emit(str(e))
                self.progress_signal.emit("Translation failed", 0)

        self.progress_bar.setMaximum(100)
        self.progress_signal.emit("Starting translation...", 0)
        threading.Thread(target=do_translate, daemon=True).start()

    def burn_subtitles(self):
        """Manages the subtitle burning process."""
        if not all([self.video_path.text(), self.srt_path.text()]):
            self.error_signal.emit("Both video and SRT files are required")
            return

        def burn():
            try:
                self.progress_signal.emit("Burning subtitles...", 50)
                self.processor.burn_subtitles(
                    self.video_path.text(),
                    self.srt_path.text(),
                    font_size=self.font_size.currentText(),
                    font_name=self.font_name.currentText(),
                    font_color=self.font_color.currentText(),
                    font_outline=self.font_outline.currentText(),
                    video_quality=self.video_quality.currentText(),
                    video_preset=self.video_preset.currentText(),
                    progress_callback=lambda status, value: self.progress_signal.emit(status, value)
                )

                self.success_signal.emit("Video processing completed!")
                self.progress_signal.emit("Ready", 0)

            except Exception as e:
                self.error_signal.emit(str(e))
                self.progress_signal.emit("Error occurred", 0)

            finally:
                self.process_button.setEnabled(True)

        self.process_button.setEnabled(False)
        self.progress_bar.setMaximum(100)
        self.progress_signal.emit("Starting burning process...", 0)
        threading.Thread(target=burn, daemon=True).start()

    def start_processing(self):
        """It handles the entire subtitle creation/burning process."""
        if not self.video_path.text():
            self.error_signal.emit("Please select a video file")
            return

        video_path = self.video_path.text()
        srt_path = self.srt_path.text()
        model_name = self.model_combo.currentText().split()[0]

        # Verify model
        if not self.processor.is_model_downloaded(model_name):
            reply = QMessageBox.question(
                self, "Model Not Found",
                f"Model {model_name} is not downloaded. Download it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.download_model()
            return

        # Check SRT file existence
        if os.path.exists(srt_path):
            reply = QMessageBox.question(
                self, "SRT File Exists",
                "SRT file already exists.\n\nUse existing file?",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                self.burn_subtitles()
                return

        def process():
            try:
                self.progress_signal.emit("Creating subtitles...", 25)
                # Create subtitles
                language = self.language_combo.currentText().split()[0]
                self.processor.create_subtitles(
                    video_path,
                    srt_path,
                    model_name,
                    language,
                    progress_callback=lambda status, value: self.progress_signal.emit(status, value)
                )

                self.progress_signal.emit("Burning subtitles...", 75)
                # Burn subtitles
                self.processor.burn_subtitles(
                    video_path,
                    srt_path,
                    font_size=self.font_size.currentText(),
                    font_name=self.font_name.currentText(),
                    font_color=self.font_color.currentText(),
                    font_outline=self.font_outline.currentText(),
                    video_quality=self.video_quality.currentText(),
                    video_preset=self.video_preset.currentText(),
                    progress_callback=lambda status, value: self.progress_signal.emit(status, value)
                )

                self.success_signal.emit("Video processing completed!")
                self.progress_signal.emit("Ready", 0)

            except Exception as e:
                self.error_signal.emit(str(e))
                self.progress_signal.emit("Error occurred", 0)

            finally:
                self.process_button.setEnabled(True)

        # Start processing
        self.process_button.setEnabled(False)
        self.progress_bar.setMaximum(100)
        self.progress_signal.emit("Starting processing...", 0)
        threading.Thread(target=process, daemon=True).start()

    def load_saved_settings(self):
        """Load saved settings."""
        try:
            settings = self.processor.load_settings()

            # Set values ​​in widgets
            self.font_size.setCurrentText(settings.get('font_size', "24"))
            self.font_name.setCurrentText(settings.get('font_name', "Arial"))
            self.font_color.setCurrentText(settings.get('font_color', "white"))
            self.font_outline.setCurrentText(settings.get('font_outline', "black"))
            self.video_quality.setCurrentText(settings.get('video_quality', "23"))
            self.video_preset.setCurrentText(settings.get('video_preset', "medium"))

            # Find and set the correct model
            model_name = settings.get('whisper_model', "base")
            for i in range(self.model_combo.count()):
                if self.model_combo.itemText(i).startswith(model_name):
                    self.model_combo.setCurrentIndex(i)
                    break

            # Find and set the correct language
            language = settings.get('whisper_language', "auto")
            for i in range(self.language_combo.count()):
                if self.language_combo.itemText(i).startswith(language):
                    self.language_combo.setCurrentIndex(i)
                    break

        except Exception as e:
            self.error_signal.emit(f"Error loading settings: {str(e)}")

    def save_current_settings(self):
        """Save the current settings."""
        try:
            settings = {
                'font_size': self.font_size.currentText(),
                'font_name': self.font_name.currentText(),
                'font_color': self.font_color.currentText(),
                'font_outline': self.font_outline.currentText(),
                'whisper_model': self.model_combo.currentText().split()[0],
                'whisper_language': self.language_combo.currentText().split()[0],
                'video_quality': self.video_quality.currentText(),
                'video_preset': self.video_preset.currentText()
            }

            self.processor.save_settings(settings)

        except Exception as e:
            self.error_signal.emit(f"Error saving settings: {str(e)}")

    def closeEvent(self, event):
        """Manages application shutdown."""
        try:
            self.save_current_settings()
            event.accept()
        except Exception as e:
            self.error_signal.emit(f"Error saving settings on close: {str(e)}")
            event.accept()
