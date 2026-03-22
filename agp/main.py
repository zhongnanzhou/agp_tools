"""
AGP - Automated Graphic Processing Tools
主程序入口
"""

import sys
from pathlib import Path

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from agp.ui.main_window import MainWindow
from agp.ui.widgets import qt_handler

import logging
from agp.utils import loggings
logger = loggings.getLogger('agp', [qt_handler, loggings.log_handlers.console_handler(logging.DEBUG)])


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    
    window.show()
    
    logger.info("AGP 启动成功")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
