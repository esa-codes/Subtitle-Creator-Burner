# gui/main_window.py

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
                           QProgressBar, QFileDialog, QGroupBox, QMessageBox, QGridLayout, QCheckBox, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal, QRunnable, QThreadPool, QObject
import os
import sys
import humanize
from pathlib import Path

from core.processor import SubtitleProcessor
from core.model_info import ModelInfo

# Worker signals class
class WorkerSignals(QObject):
    progress = pyqtSignal(str, int)
    error = pyqtSignal(str)
    success = pyqtSignal(str)
    finished = pyqtSignal()

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add kwargs progress callback if supported
        if 'progress_callback' in kwargs:
            kwargs['progress_callback'] = lambda status, value: self.signals.progress.emit(status, value)

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            if result:
                self.signals.success.emit(str(result))
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

class SubtitleGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Creator & Burner")
        self.setMinimumSize(800, 600)

        # Initialize thread pool
        self.threadpool = QThreadPool()

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
        self.process_button.setEnabled(True)
        self.download_button.setEnabled(True)

    def _show_success(self, message: str):
        """Show success messages in a thread-safe manner."""
        QMessageBox.information(self, "Success", message)
        self.process_button.setEnabled(True)
        self.download_button.setEnabled(True)

    def _update_ui(self):
        """Update UI elements in a thread-safe manner."""
        self.update_model_status()
        self.process_button.setEnabled(True)
        self.download_button.setEnabled(True)

    def download_model(self):
        """Manages the download of the selected model."""
        selected = self.model_combo.currentText().split()[0]

        def do_download():
            try:
                worker.signals.progress.emit(f"Starting download of {selected} model...", 0)
                worker.signals.progress.emit(f"Downloading {selected} model...", 20)
                self.processor.download_model(selected)
                worker.signals.progress.emit(f"Model {selected} downloaded successfully!", 100)
                worker.signals.success.emit(f"Model {selected} downloaded successfully!")
            except Exception as e:
                worker.signals.error.emit(str(e))

        worker = Worker(do_download)
        worker.signals.progress.connect(self._update_progress)
        worker.signals.error.connect(self._show_error)
        worker.signals.success.connect(self._show_success)
        worker.signals.finished.connect(self._update_ui)

        self.download_button.setEnabled(False)
        self.process_button.setEnabled(False)
        self.progress_bar.setMaximum(100)
        self._update_progress("Preparing download...", 0)

        self.threadpool.start(worker)

    def translate_srt(self):
        """Manages subtitle translation."""
        try:
            # Validation checks
            if not self.srt_path.text():
                self._show_error("No SRT file selected")
                return

            if not os.path.exists(self.srt_path.text()):
                self._show_error("Selected SRT file does not exist")
                return

            def do_translate():
                try:
                    worker.signals.progress.emit("Starting translation...", 10)
                    worker.signals.progress.emit("Translating subtitles...", 30)

                    output_file = self.processor.translate_subtitles(
                        self.srt_path.text(),
                        self.trans_from.currentText(),
                        self.trans_to.currentText()
                    )

                    worker.signals.progress.emit("Translation completed!", 100)
                    return output_file

                except Exception as e:
                    worker.signals.error.emit(f"Translation error: {str(e)}")
                    return None

            worker = Worker(do_translate)
            worker.signals.progress.connect(self._update_progress)
            worker.signals.error.connect(self._show_error)
            worker.signals.success.connect(self._handle_translation_complete)
            worker.signals.finished.connect(lambda: self._update_progress("Ready", 100))

            self.progress_bar.setMaximum(100)
            self._update_progress("Preparing translation...", 0)

            self.threadpool.start(worker)

        except Exception as e:
            self._show_error(f"Error initializing translation: {str(e)}")

    def _handle_translation_complete(self, output_file):
        """Handle translation completion and ask user about using the translated file."""
        if output_file and os.path.exists(output_file):
            reply = QMessageBox.question(
                self, "Success",
                f"Translation completed!\nUse translated file?\n{output_file}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.srt_path.setText(output_file)
        else:
            self._show_error("Translation failed - output file not found")

    def burn_subtitles(self):
        if not all([self.video_path.text(), self.srt_path.text()]):
            self._show_error("Both video and SRT files are required")
            return

        def do_burn():
            try:
                worker.signals.progress.emit("Burning subtitles...", 50)
                self.processor.burn_subtitles(
                    self.video_path.text(),
                    self.srt_path.text(),
                    font_size=self.font_size.currentText(),
                    font_name=self.font_name.currentText(),
                    font_color=self.font_color.currentText(),
                    font_outline=self.font_outline.currentText(),
                    video_quality=self.video_quality.currentText(),
                    video_preset=self.video_preset.currentText(),
                    background_color=self.background_color.currentText(),
                    uppercase=self.uppercase_option.isChecked(),
                    word_by_word=self.word_by_word_option.isChecked(),
                    subtitle_position=self.subtitle_position.currentText(),
                    margin_left=self.margin_slider.value(),  # Pass slider value
                    progress_callback=lambda status, value: worker.signals.progress.emit(status, value)
                )

                worker.signals.success.emit("Video processing completed!")
            except Exception as e:
                worker.signals.error.emit(str(e))

        worker = Worker(do_burn)
        worker.signals.progress.connect(self._update_progress)
        worker.signals.error.connect(self._show_error)
        worker.signals.success.connect(self._show_success)
        worker.signals.finished.connect(lambda: self._update_progress("Ready", 0))

        self.process_button.setEnabled(False)
        self.progress_bar.setMaximum(100)
        self._update_progress("Starting burning process...", 0)

        self.threadpool.start(worker)

    def start_processing(self):
        """Handles the entire subtitle creation/burning process."""
        # Validate video file selection
        if not self.video_path.text():
            self._show_error("Please select a video file")
            return

        video_path = self.video_path.text()
        srt_path = self.srt_path.text()
        model_name = self.model_combo.currentText().split()[0]

        # Verify model download status
        if not self.processor.is_model_downloaded(model_name):
            reply = QMessageBox.question(
                self, "Model Not Found",
                f"Model {model_name} is not downloaded. Download it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.download_model()
            return

        # Check if SRT file already exists
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

        def do_process():
            try:
                # Phase 1: Create subtitles (0-50% progress)
                worker.signals.progress.emit("Preparing for subtitle creation...", 0)
                language = self.language_combo.currentText().split()[0]

                def subtitle_progress(status, value):
                    # Scale progress from 0-100 to 0-50
                    scaled_value = value // 2
                    worker.signals.progress.emit(f"Creating subtitles: {status}", scaled_value)

                # Create subtitles
                worker.signals.progress.emit("Initializing Whisper model...", 5)
                self.processor.create_subtitles(
                    video_path,
                    srt_path,
                    model_name,
                    language,
                    progress_callback=subtitle_progress
                )

                # Phase 2: Burn subtitles (50-100% progress)
                worker.signals.progress.emit("Preparing for subtitle burning...", 50)

                # Burn subtitles phase
                self.processor.burn_subtitles(
                    video_path,
                    srt_path,
                    font_size=self.font_size.currentText(),
                    font_name=self.font_name.currentText(),
                    font_color=self.font_color.currentText(),
                    font_outline=self.font_outline.currentText(),
                    video_quality=self.video_quality.currentText(),
                    video_preset=self.video_preset.currentText(),
                    background_color=self.background_color.currentText(),
                    uppercase=self.uppercase_option.isChecked(),
                    word_by_word=self.word_by_word_option.isChecked(),
                    progress_callback=burn_progress
                )

                def burn_progress(status, value):
                    # Scale progress from 0-100 to 50-100
                    scaled_value = 50 + (value // 2)
                    worker.signals.progress.emit(f"Burning subtitles: {status}", scaled_value)

                # Burn subtitles into video
                self.processor.burn_subtitles(
                    video_path,
                    srt_path,
                    font_size=self.font_size.currentText(),
                    font_name=self.font_name.currentText(),
                    font_color=self.font_color.currentText(),
                    font_outline=self.font_outline.currentText(),
                    video_quality=self.video_quality.currentText(),
                    video_preset=self.video_preset.currentText(),
                    progress_callback=burn_progress
                )

                # Signal completion
                worker.signals.progress.emit("Processing completed successfully!", 100)
                worker.signals.success.emit("Video processing completed successfully!")

            except Exception as e:
                # Handle any errors during processing
                error_message = f"Error during processing: {str(e)}"
                worker.signals.error.emit(error_message)
                worker.signals.progress.emit("Processing failed", 0)

        # Create and configure worker
        worker = Worker(do_process)
        worker.signals.progress.connect(self._update_progress)
        worker.signals.error.connect(self._show_error)
        worker.signals.success.connect(self._show_success)
        worker.signals.finished.connect(lambda: self._update_progress("Ready", 100))

        # Prepare UI for processing
        self.process_button.setEnabled(False)
        self.progress_bar.setMaximum(100)
        self._update_progress("Initializing processing...", 0)

        # Start processing in background
        self.threadpool.start(worker)

    def closeEvent(self, event):
        """Manages application shutdown."""
        try:
            self.save_current_settings()
            # Wait for all threads to complete
            self.threadpool.waitForDone()
            event.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during shutdown: {str(e)}")
            event.accept()

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
        """Create the Whisper model settings section."""
        group = QGroupBox("Whisper Model Settings")
        layout = QGridLayout()

        # Model selection
        self.model_combo = QComboBox()
        models = list(ModelInfo.SIZES.keys())
        model_infos = [ModelInfo.get_model_info(m) for m in models]
        self.model_combo.addItems(model_infos)
        self.model_combo.currentIndexChanged.connect(self._update_ui)

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

        # Background color
        self.background_color = QComboBox()
        self.background_color.addItems(["none", "black", "white", "gray"])
        layout.addWidget(QLabel("Background:"), 2, 0)
        layout.addWidget(self.background_color, 2, 1)

        # Uppercase option
        self.uppercase_option = QCheckBox("Uppercase")
        layout.addWidget(self.uppercase_option, 2, 2)

        # Word-by-word option
        self.word_by_word_option = QCheckBox("Word by Word")
        layout.addWidget(self.word_by_word_option, 2, 3)

        # Subtitle position
        self.subtitle_position = QComboBox()
        self.subtitle_position.addItems(["bottom", "top center"])
        layout.addWidget(QLabel("Position:"), 3, 0)
        layout.addWidget(self.subtitle_position, 3, 1)

        # Add MarginL slider
        self.margin_slider = QSlider(Qt.Orientation.Horizontal)
        self.margin_slider.setMinimum(0)  # Min margin
        self.margin_slider.setMaximum(500)  # Max margin
        self.margin_slider.setValue(200)  # Default margin
        self.margin_slider.valueChanged.connect(self.update_margin_label)

        self.margin_label = QLabel("MarginL: 200")  # Label to show current value
        layout.addWidget(self.margin_label, 4, 0, 1, 2)
        layout.addWidget(self.margin_slider, 4, 2, 1, 2)

        group.setLayout(layout)
        return group

    def update_margin_label(self):
        """Update the MarginL label based on slider value."""
        value = self.margin_slider.value()
        self.margin_label.setText(f"MarginL: {value}")


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

        self.process_button = QPushButton("Create and burn subtitles")
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

    def load_saved_settings(self):
        """Load saved settings."""
        try:
            settings = self.processor.load_settings()

            # Set values in widgets
            self.font_size.setCurrentText(settings.get('font_size', "24"))
            self.font_name.setCurrentText(settings.get('font_name', "Arial"))
            self.font_color.setCurrentText(settings.get('font_color', "white"))
            self.font_outline.setCurrentText(settings.get('font_outline', "black"))
            self.background_color.setCurrentText(settings.get('background_color', "none"))
            self.uppercase_option.setChecked(settings.get('uppercase', False))
            self.word_by_word_option.setChecked(settings.get('word_by_word', False))
            self.subtitle_position.setCurrentText(settings.get('subtitle_position', "bottom"))
            self.video_quality.setCurrentText(settings.get('video_quality', "23"))
            self.video_preset.setCurrentText(settings.get('video_preset', "medium"))

            # Set MarginL value
            margin_left = settings.get('margin_left', 200)  # Default to 200
            self.margin_slider.setValue(margin_left)
            self.margin_label.setText(f"MarginL: {margin_left}")

            # Set model and language
            model_name = settings.get('whisper_model', "base")
            for i in range(self.model_combo.count()):
                if self.model_combo.itemText(i).startswith(model_name):
                    self.model_combo.setCurrentIndex(i)
                    break

            language = settings.get('whisper_language', "auto")
            for i in range(self.language_combo.count()):
                if self.language_combo.itemText(i).startswith(language):
                    self.language_combo.setCurrentIndex(i)
                    break

        except Exception as e:
            self._show_error(f"Error loading settings: {str(e)}")


    def save_current_settings(self):
        """Save the current settings."""
        try:
            settings = {
                'font_size': self.font_size.currentText(),
                'font_name': self.font_name.currentText(),
                'font_color': self.font_color.currentText(),
                'font_outline': self.font_outline.currentText(),
                'background_color': self.background_color.currentText(),
                'uppercase': self.uppercase_option.isChecked(),
                'word_by_word': self.word_by_word_option.isChecked(),
                'whisper_model': self.model_combo.currentText().split()[0],
                'whisper_language': self.language_combo.currentText().split()[0],
                'video_quality': self.video_quality.currentText(),
                'video_preset': self.video_preset.currentText(),
                'subtitle_position': self.subtitle_position.currentText(),
                'margin_left': self.margin_slider.value()
            }

            self.processor.save_settings(settings)

        except Exception as e:
            self._show_error(f"Error saving settings: {str(e)}")
