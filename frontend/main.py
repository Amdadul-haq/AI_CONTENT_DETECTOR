import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, 
    QFileDialog, QMessageBox, QProgressBar, QHBoxLayout, QFrame, 
    QSplitter, QGridLayout, QGroupBox, QTabWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QTextCharFormat, QTextCursor
import requests
import pdfplumber
import qdarkstyle

class ModernButton(QPushButton):
    def __init__(self, text, icon_path=None):
        super().__init__(text)
        self.setMinimumHeight(40)
        self.setFont(QFont('Segoe UI', 10))
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(20, 20))
        
        # Style the button
        self.setStyleSheet("""
            QPushButton {
                background-color: #4a6cd4;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #3a5bc4;
            }
            QPushButton:pressed {
                background-color: #2a4bb4;
            }
        """)

class AIDetectorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.last_result = None
        
    def init_ui(self):
        self.setWindowTitle('AI Content Detector')
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Arial';
                font-size: 10pt;
            }
            QLabel {
                font-size: 11pt;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px;
                background-color: #f9f9f9;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                                stop:0 #4a6cd4, stop:1 #5a7ce4);
                border-radius: 5px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("AI Content Detector")
        header.setFont(QFont('Segoe UI', 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #4a6cd4; margin-bottom: 10px;")
        main_layout.addWidget(header)
        
        # Description
        description = QLabel("Upload text or a PDF file to analyze for AI-generated content")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #666; margin-bottom: 15px;")
        main_layout.addWidget(description)
        
        # Content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Text input
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        
        input_group = QGroupBox("Text Input")
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        input_layout = QVBoxLayout(input_group)
        
        # Text Edit Box
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText('Enter text or upload a PDF...')
        self.text_edit.setMinimumHeight(300)
        input_layout.addWidget(self.text_edit)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Upload PDF Button
        self.upload_button = ModernButton('Upload PDF')
        self.upload_button.clicked.connect(self.upload_pdf)
        buttons_layout.addWidget(self.upload_button)
        
        # Detect AI Content Button
        self.detect_button = ModernButton('Detect AI Content')
        self.detect_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.detect_button.clicked.connect(self.detect_ai)
        buttons_layout.addWidget(self.detect_button)
        
        # Clear Button
        self.clear_button = ModernButton('Clear')
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
            QPushButton:pressed {
                background-color: #d32f2f;
            }
        """)
        self.clear_button.clicked.connect(self.clear_text)
        buttons_layout.addWidget(self.clear_button)
        
        input_layout.addLayout(buttons_layout)
        left_layout.addWidget(input_group)
        
        # Right panel - Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        results_group = QGroupBox("Analysis Results")
        results_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        results_layout = QVBoxLayout(results_group)
        
        # AI Score
        score_label = QLabel("AI Content Score:")
        score_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        results_layout.addWidget(score_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setTextVisible(True)
        results_layout.addWidget(self.progress_bar)
        
        # Score interpretation
        self.score_interpretation = QLabel("Waiting for analysis...")
        self.score_interpretation.setWordWrap(True)
        self.score_interpretation.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        results_layout.addWidget(self.score_interpretation)
        
        # Detailed scores
        details_label = QLabel("Detailed Analysis:")
        details_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        results_layout.addWidget(details_label)
        
        # Create a grid for detailed scores
        details_grid = QGridLayout()
        details_grid.setSpacing(10)
        
        # Sentence variety
        details_grid.addWidget(QLabel("Sentence Variety:"), 0, 0)
        self.sentence_variety_bar = QProgressBar()
        self.sentence_variety_bar.setRange(0, 100)
        self.sentence_variety_bar.setValue(0)
        details_grid.addWidget(self.sentence_variety_bar, 0, 1)
        
        # Word repetition
        details_grid.addWidget(QLabel("Word Repetition:"), 1, 0)
        self.word_repetition_bar = QProgressBar()
        self.word_repetition_bar.setRange(0, 100)
        self.word_repetition_bar.setValue(0)
        details_grid.addWidget(self.word_repetition_bar, 1, 1)
        
        # Transition usage
        details_grid.addWidget(QLabel("Transition Usage:"), 2, 0)
        self.transition_usage_bar = QProgressBar()
        self.transition_usage_bar.setRange(0, 100)
        self.transition_usage_bar.setValue(0)
        details_grid.addWidget(self.transition_usage_bar, 2, 1)
        
        # Burstiness
        details_grid.addWidget(QLabel("Burstiness:"), 3, 0)
        self.burstiness_bar = QProgressBar()
        self.burstiness_bar.setRange(0, 100)
        self.burstiness_bar.setValue(0)
        details_grid.addWidget(self.burstiness_bar, 3, 1)
        
        results_layout.addLayout(details_grid)
        
        # Highlighted sections
        highlighted_label = QLabel("Highlighted AI Sections:")
        highlighted_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        results_layout.addWidget(highlighted_label)
        
        self.highlighted_sections = QTextEdit()
        self.highlighted_sections.setReadOnly(True)
        self.highlighted_sections.setMaximumHeight(150)
        self.highlighted_sections.setStyleSheet("background-color: #f9f9f9;")
        results_layout.addWidget(self.highlighted_sections)
        
        # Download Report Button
        self.download_button = ModernButton('Download Report')
        self.download_button.clicked.connect(self.download_report)
        results_layout.addWidget(self.download_button)
        
        right_layout.addWidget(results_group)
        
        # Add panels to splitter
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([450, 450])
        
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("color: #666; padding: 5px; border-top: 1px solid #ccc;")
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
    def upload_pdf(self):
        """Upload and extract text from a PDF file"""
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if file_name:
            try:
                self.status_bar.setText(f"Loading PDF: {os.path.basename(file_name)}...")
                QApplication.processEvents()
                
                with pdfplumber.open(file_name) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    self.text_edit.setPlainText(text)
                
                self.status_bar.setText(f"PDF loaded: {os.path.basename(file_name)}")
            except Exception as e:
                self.status_bar.setText("Error loading PDF")
                QMessageBox.critical(self, "Error", f"Failed to read PDF: {str(e)}")
    
    def clear_text(self):
        """Clear the text input and reset results"""
        self.text_edit.clear()
        self.progress_bar.setValue(0)
        self.sentence_variety_bar.setValue(0)
        self.word_repetition_bar.setValue(0)
        self.transition_usage_bar.setValue(0)
        self.burstiness_bar.setValue(0)
        self.highlighted_sections.clear()
        self.score_interpretation.setText("Waiting for analysis...")
        self.status_bar.setText("Ready")
        self.last_result = None

    def detect_ai(self):
        """Detect AI-generated content"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter text or upload a PDF")
            return
        
        self.status_bar.setText("Analyzing text...")
        QApplication.processEvents()
        
        response = self.send_to_backend(text)
        if response:
            if "error" in response:
                self.status_bar.setText("Error in analysis")
                QMessageBox.critical(self, "Error", response["error"])
            else:
                self.last_result = response
                self.update_results(response)
                self.status_bar.setText("Analysis complete")

    def send_to_backend(self, text):
        """Send text to the backend API for AI detection"""
        try:
            url = "http://localhost:5000/api/detect_ai"
            response = requests.post(url, json={"text": text}, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Failed to connect to backend: {str(e)}"}

    def update_results(self, result):
        """Update the UI with detection results"""
        ai_percentage = result.get('ai_percentage', 0)
        
        # Animate progress bar
        current = self.progress_bar.value()
        step = 1 if current < ai_percentage else -1
        
        # Update progress bar color based on value
        if ai_percentage < 30:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                                    stop:0 #4CAF50, stop:1 #8BC34A);
                }
            """)
        elif ai_percentage < 70:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                                    stop:0 #FFC107, stop:1 #FFEB3B);
                }
            """)
        else:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                                    stop:0 #F44336, stop:1 #FF5722);
                }
            """)
        
        # Set the value directly for now (animation can be added later)
        self.progress_bar.setValue(ai_percentage)
        
        # Update interpretation
        if ai_percentage < 30:
            interpretation = "This content appears to be mostly human-written."
        elif ai_percentage < 50:
            interpretation = "This content shows some characteristics of AI-generated text, but is likely mostly human-written."
        elif ai_percentage < 70:
            interpretation = "This content has a moderate likelihood of being AI-generated or heavily edited AI content."
        else:
            interpretation = "This content has a high likelihood of being AI-generated."
        
        self.score_interpretation.setText(interpretation)
        
        # Update detailed scores
        details = result.get('details', {})
        self.sentence_variety_bar.setValue(details.get('sentence_variety', 0))
        self.word_repetition_bar.setValue(details.get('word_repetition', 0))
        self.transition_usage_bar.setValue(details.get('transition_usage', 0))
        self.burstiness_bar.setValue(details.get('burstiness', 0))
        
        # Update highlighted sections
        highlighted_sections = result.get('highlighted_sections', [])
        if highlighted_sections:
            self.highlighted_sections.clear()
            for section in highlighted_sections:
                self.highlighted_sections.append(f"• {section}\n\n")
        else:
            self.highlighted_sections.setText("No specific AI-generated sections identified.")

    def download_report(self):
        """Download the analysis report as a text file"""
        if not self.last_result:
            QMessageBox.warning(self, "Warning", "Please analyze text before downloading a report")
            return
            
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt)")
        if file_name:
            try:
                ai_percentage = self.last_result.get('ai_percentage', 0)
                details = self.last_result.get('details', {})
                highlighted_sections = self.last_result.get('highlighted_sections', [])
                
                report_content = (
                    f"AI Content Detection Report\n"
                    f"==========================\n\n"
                    f"Overall AI Score: {ai_percentage}%\n\n"
                    f"Detailed Analysis:\n"
                    f"- Sentence Variety: {details.get('sentence_variety', 0)}%\n"
                    f"- Word Repetition: {details.get('word_repetition', 0)}%\n"
                    f"- Transition Usage: {details.get('transition_usage', 0)}%\n"
                    f"- Burstiness: {details.get('burstiness', 0)}%\n\n"
                    f"Interpretation:\n{self.score_interpretation.text()}\n\n"
                    f"Highlighted AI Sections:\n"
                )
                
                if highlighted_sections:
                    for section in highlighted_sections:
                        report_content += f"• {section}\n\n"
                else:
                    report_content += "No specific AI-generated sections identified.\n\n"
                
                report_content += (
                    f"Analyzed Text (first 1000 chars):\n"
                    f"--------------------------------\n"
                    f"{self.text_edit.toPlainText()[:1000]}...\n\n"
                    f"Report generated by AI Content Detector"
                )
                
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(report_content)
                
                self.status_bar.setText(f"Report saved to {os.path.basename(file_name)}")
                QMessageBox.information(self, "Success", f"Report saved to {file_name}")
            except Exception as e:
                self.status_bar.setText("Error saving report")
                QMessageBox.critical(self, "Error", f"Failed to save report: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Apply dark style if preferred
    # Uncomment the next line to use dark mode
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    window = AIDetectorApp()
    window.show()
    sys.exit(app.exec_())
