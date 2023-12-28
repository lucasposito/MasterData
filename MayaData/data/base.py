from PySide2 import QtWidgets
from shiboken2 import wrapInstance

from maya import OpenMayaUI

import json
import sys


maya_window = OpenMayaUI.MQtUtil.mainWindow()
if sys.version_info.major >= 3:
    maya_window = wrapInstance(int(maya_window), QtWidgets.QWidget)
else:
    maya_window = wrapInstance(long(maya_window), QtWidgets.QWidget)

    
file_filter = 'Json (*.json)'
dialog = QtWidgets.QDialog(maya_window)


class BaseData(dict):
    def __init__(self, *args, **kwargs):
        super(BaseData, self).__init__(*args, **kwargs)
        
    def save(self):
        file_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(dialog, 'Select File', '', file_filter)
        if not file_path:
            return
        with open(file_path, 'w') as f:
            f.write(json.dumps(self, indent=4))

    def load(self):
        file_path, selected_filter = QtWidgets.QFileDialog.getOpenFileName(dialog, 'Select File', '', file_filter)
        if not file_path:
            return
        with open(file_path, 'r') as f:
            self.update(json.loads(f.read()))
