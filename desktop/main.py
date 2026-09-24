import sys, json
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication,QMainWindow,QTabWidget,QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QPushButton,QTextEdit,QLabel,QFormLayout,QSpinBox,QComboBox,QFileDialog,QMessageBox,QGroupBox
from api_client import WebhookClient,WebhookError
from workflow import load,save,validate

class Main(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('G-Labs Studio'); self.resize(1180,760); self.client=None; self._build()
    def _build(self):
        tabs=QTabWidget(); tabs.addTab(self.dashboard(),'Studio'); tabs.addTab(self.workflow_tab(),'Workflow'); tabs.addTab(self.webhook_tab(),'Webhook'); tabs.addTab(self.settings_tab(),'Settings'); self.setCentralWidget(tabs)
    def dashboard(self):
        w=QWidget(); l=QVBoxLayout(w); title=QLabel('G-Labs Studio'); title.setStyleSheet('font-size:30px;font-weight:700'); l.addWidget(title)
        sub=QLabel('Official desktop workspace for authorized G-Labs Webhook and Workflow automation.'); l.addWidget(sub)
        box=QGroupBox('Services'); f=QFormLayout(box)
        for name in ['Image','Video','Grok','Meta AI','OpenAI','Upscale','Workflow Engine']:
            f.addRow(name,QLabel('Ready for configured Webhook server'))
        l.addWidget(box); l.addStretch(); return w
    def webhook_tab(self):
        w=QWidget(); l=QVBoxLayout(w); f=QFormLayout(); self.url=QLineEdit('http://127.0.0.1:8765'); self.key=QLineEdit(); self.key.setEchoMode(QLineEdit.Password); f.addRow('Server URL',self.url); f.addRow('API Key',self.key); l.addLayout(f)
        row=QHBoxLayout(); b=QPushButton('Check Health'); b.clicked.connect(self.health); row.addWidget(b); self.kind=QComboBox(); self.kind.addItems(['image','video','grok','meta','openai','upscale']); row.addWidget(self.kind); l.addLayout(row)
        self.prompt=QTextEdit(); self.prompt.setPlaceholderText('Prompt / JSON payload'); l.addWidget(self.prompt); send=QPushButton('Submit'); send.clicked.connect(self.submit); l.addWidget(send); self.log=QTextEdit(); self.log.setReadOnly(True); l.addWidget(self.log); return w
    def client_now(self): return WebhookClient(self.url.text(),self.key.text())
    def health(self):
        try: self.log.append(json.dumps(self.client_now().health(),ensure_ascii=False,indent=2))
        except Exception as e: self.log.append(str(e))
    def submit(self):
        try:
            raw=self.prompt.toPlainText().strip(); payload=json.loads(raw) if raw.startswith('{') else {'prompt':raw}; r=self.client_now().generate(self.kind.currentText(),payload); self.log.append(json.dumps(r,ensure_ascii=False,indent=2))
        except Exception as e: self.log.append(str(e))
    def workflow_tab(self):
        w=QWidget(); l=QVBoxLayout(w); row=QHBoxLayout(); openb=QPushButton('Open Flow'); openb.clicked.connect(self.open_flow); saveb=QPushButton('Save Flow'); saveb.clicked.connect(self.save_flow); val=QPushButton('Validate'); val.clicked.connect(self.validate_flow); row.addWidget(openb); row.addWidget(saveb); row.addWidget(val); l.addLayout(row); self.flow=QTextEdit(); l.addWidget(self.flow); self.flow_status=QLabel('No workflow loaded'); l.addWidget(self.flow_status); return w
    def open_flow(self):
        p,_=QFileDialog.getOpenFileName(self,'Open Workflow','','JSON (*.json)');
        if not p:return
        try:self.flow.setPlainText(Path(p).read_text(encoding='utf-8')); self.flow_status.setText(p); self.validate_flow()
        except Exception as e: QMessageBox.critical(self,'Open error',str(e))
    def save_flow(self):
        p,_=QFileDialog.getSaveFileName(self,'Save Workflow','','JSON (*.json)');
        if not p:return
        try: doc=json.loads(self.flow.toPlainText()); save(doc,p); self.flow_status.setText(p)
        except Exception as e: QMessageBox.critical(self,'Save error',str(e))
    def validate_flow(self):
        try: doc=json.loads(self.flow.toPlainText()); er,wa=validate(doc); self.flow_status.setText(('VALID' if not er else 'INVALID')+' | '+('; '.join(er+wa) if er+wa else 'No issues')); 
        except Exception as e:self.flow_status.setText('JSON ERROR: '+str(e))
    def settings_tab(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel('G-Labs Studio configuration')); l.addWidget(QLabel('API credentials are kept local to this application. This project does not collect browser cookies, session tokens, or CAPTCHA tokens.')); l.addStretch(); return w

app=QApplication(sys.argv); app.setStyle('Fusion'); win=Main(); win.show(); sys.exit(app.exec())
