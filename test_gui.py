"""
Простой тест GUI
"""

import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton

def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle('Тест GUI')
    window.setGeometry(100, 100, 300, 200)
    
    layout = QVBoxLayout()
    
    label = QLabel('Если вы видите это окно, GUI работает!')
    label.setStyleSheet('font-size: 14px; padding: 20px;')
    layout.addWidget(label)
    
    btn = QPushButton('Закрыть')
    btn.clicked.connect(window.close)
    layout.addWidget(btn)
    
    window.setLayout(layout)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()