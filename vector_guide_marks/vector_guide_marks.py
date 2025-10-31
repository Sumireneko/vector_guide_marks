# ================================================
# Krita Vector Guide Marks plug-in (GUI) v0.58
# ================================================
# Copyright (C) 2025 L.Sumireneko.M
# This program is free software: you can redistribute it and/or modify it under the 
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>. 
from functools import partial
import krita
import os

try:
    if int(krita.qVersion().split('.')[0]) == 5:
        raise
    from PyQt6 import uic
    from PyQt6.QtCore import QObject, QEvent, QTimer, QSignalBlocker, pyqtSignal
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QTextEdit, QVBoxLayout, QPushButton, QRadioButton, QButtonGroup
    )
    from PyQt6.QtGui import QTransform
    from PyQt6.QtGui import QIntValidator
except:
    from PyQt5 import uic
    from PyQt5.QtCore import QObject, QEvent, QTimer, QSignalBlocker, pyqtSignal
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QTextEdit, QVBoxLayout, QPushButton, QRadioButton, QButtonGroup
    )
    from PyQt5.QtGui import QTransform
    from PyQt5.QtGui import QIntValidator

from krita import *
from .size_data import sizes,fixed_sizes,preset_menu_entry,paper_menu_entry
from . import script_main

ac_color = "#CCCCCC"
is_dark = False

# Example configuration
params = {
    'mode':'direct',
    'preset':'Free',
    'size_type': 'Sizes', # 'B4' etc

    'dpi': 72,
    'use_bleed': True,
    'bleed': 3,#default 3mm
    'lenCorner': 7,# length of the corner trim-marks
    'centerWing': 18,
    'centerPerp': 4.5,
    'centerOffset': 2,
    'stroke': 0.5,
    'crop_style': 'default', # 'jp_trim' or 'default'
    'size_mode': 'paper',# default or paper
    'size_dir': 'vertical',
    'prefix':'preview_',
    'frame': False,
    'slice': False,
    'vcol_split':1,# It should be 1
    'vrow_split':1,# It should be 1
    'vcol_spc':1,
    'vrow_spc':1,
    'vtotal_w':1,
    'vtotal_h':1,
    'vunit_w':1,
    'vunit_h':1,


    'vcol_spc_mm': 12.0,     # Display
    'vcol_spc_inch': 0.472,  # Display
    'vcol_spc_px': 45.3,      # Display

    'vrow_spc_mm': 12.0,     # Display
    'vrow_spc_inch': 0.472,  # Display
    'vrow_spc_px': 45.3,      # Display

    'vtotal_w_mm': 12.0,     # Display
    'vtotal_w_inch': 0.472,  # Display
    'vtotal_w_px': 45.3,      # Display

    'vtotal_h_mm': 12.0,     # Display
    'vtotal_h_inch': 0.472,  # Display
    'vtotal_h_px': 45.3,      # Display


    'vunit_w_mm': 12.0,     # Display
    'vunit_w_inch': 0.472,  # Display
    'vunit_w_px': 45.3,      # Display

    'vunit_h_mm': 12.0,     # Display
    'vunit_h_inch': 0.472,  # Display
    'vunit_h_px': 45.3,      # Display

    'txt_capa': False,
    'ignore_shape': False,
    'grid_size_mode': "unit",
    'use_guide': False,
    'info': True,
    'dimension': False,
    'dim_scale': True,
    'dim_scale_factor': 1,
    'dim_w': True,
    'dim_h': True,

    'dbg_wpad': 0.53,
    'dbg_dpad': 3.05,

    'unit_mode':'mm',
    'old_unit_mode':'mm',

    'rounded_corners':False,
    'roundness': 0,

    'unit_cut_guide':False,
    'mod_grid_guide':False,

    'preview':True

}

class LogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Infomation")
        self.resize(400, 300)

        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(self.text_area)
        layout.addWidget(close_button)
        self.setLayout(layout)

    def append_log(self, message):
        self.text_area.append(message)

    def clear_log(self):
        self.text_area.clear()

    def closeEvent(self, event):
        if self.parent():
            self.parent().log_window = None
        super().closeEvent(event)



class WheelBlocker(QObject):
    def eventFilter(self, obj, event):
        return event.type() == QEvent.Wheel

class create_VectorGuidMarksDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        global params,ac_color,is_dark
        params['size_mode'] = "paper"
        self.setWindowTitle("Vector Guide Marks settings")
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.centralWidget = uic.loadUi( os.path.join(os.path.dirname(os.path.realpath(__file__)),"user_interface.ui"))

        is_dark = is_ui_color_dark(self)
        ac_color = "#CCCCCC" if is_dark== True else "#111111"


        # Temporary state（This dict can store preview-ID and various data for input field value）
        # self.preview_state = {}
        self.preview_state = PreviewState()

        self.log_window = None 

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.centralWidget)
        self.setLayout(self.layout)


        self.infoBtn = self.findChild(QPushButton, "infoButton")
        self.infoBtn.clicked.connect(self.get_all_info)
        self.infoBtn.setFixedSize(60, 25)


        # Size
        self.labelSize = self.findChild(QLabel, "labelSize")
        self.comboSize = self.findChild(QComboBox, "comboSize")

        # Preset
        self.labelPreset = self.findChild(QLabel, "labelPreset")
        self.comboPreset = self.findChild(QComboBox, "comboPreset")

        # set menu entries
        self.preset_papers = paper_menu_entry
        self.preset_list = preset_menu_entry
        self.create_combobox_with_separators(self.comboPreset, self.preset_list)


        # update
        default_preset = params.get("preset", "US")
        self.comboPreset.setCurrentText(default_preset)
        self.updateSizeOptions(default_preset)
        self.comboPreset.currentTextChanged.connect(self.onPresetChanged)


        # set default (if it exist in there)
        s_idx = sizes.index(params["size_type"]) if params["size_type"] in sizes else 0
        text = "A4"# sizes[s_idx]
        self.comboSize.setCurrentIndex(s_idx) # default
        self.comboSize.currentTextChanged.connect(lambda text: self.on_value_changed("size_type", text))



        # Orientation (Vertical / Horizontal)
        self.radioVertical = self.findChild(QRadioButton, "radioVertical")
        self.radioHorizontal = self.findChild(QRadioButton, "radioHorizontal")
        
        # Bleed checkbox
        self.checkBleed = self.findChild(QCheckBox, "checkBleed")
        self.checkBleed.setChecked(params['use_bleed'])  # make chaked
        font = self.checkBleed.font()
        font.setBold(True)
        self.checkBleed.setFont(font)

        self.checkBleed.stateChanged.connect(
            lambda state: self.on_value_changed("use_bleed", state ==  Qt.Checked)
        )

        #self.lineBleed = self.findChild(QLineEdit, "lineBleed")
        #self.lineBleed.setValidator(QIntValidator(-9999, 9999))
        #self.lineBleed.setText(str(params["bleed"]))
        #self.lineBleed.setDisabled(True)

        #self.lineBleed.editingFinished.connect(lambda: self.on_value_changed("bleed", self.lineBleed.text()))
        #self.lineBleed.setFixedWidth(120) 

        # Tonbo style (Default or Japanese)
        self.radioDefault = self.findChild(QRadioButton, "radioDefault")
        self.radioJapanese = self.findChild(QRadioButton, "radioJapanese")

        # Guide checkbox
        self.checkGuide = self.findChild(QCheckBox, "checkGuide")
        self.checkGuide.setChecked(params['use_guide'])  # make chaked
        self.checkGuide.stateChanged.connect(
            lambda state: self.on_value_changed("use_guide", state ==  Qt.Checked)
        )

        # Guide checkbox
        self.checkGuide2 = self.findChild(QCheckBox, "checkGuide2")
        self.checkGuide2.setChecked(params['unit_cut_guide'])  # make chaked
        self.checkGuide2.stateChanged.connect(
            lambda state: self.on_value_changed("unit_cut_guide", state ==  Qt.Checked)
        )


        
        # Preview checkbox
        self.checkPreview = self.findChild(QCheckBox, "checkPreview")
        self.checkPreview.setChecked(params['preview'])  # make chaked
        self.checkPreview.stateChanged.connect(
            lambda state: self.on_value_changed("preview", state ==  Qt.Checked)
        )

        # Frame checkbox
        self.checkFrame = self.findChild(QCheckBox, "checkFrame")
        self.checkFrame.setChecked(params['frame'])  # make chaked
        self.checkFrame.stateChanged.connect(
            lambda state: self.on_value_changed("frame", state ==  Qt.Checked)
        )


        self.comboUnit = self.findChild(QComboBox, "comboUnit")
        unit_list=["mm","px","inch"]
        self.create_combobox_with_separators(self.comboUnit, unit_list)
        u_idx = unit_list.index(params["unit_mode"]) if params["unit_mode"] in unit_list else 0
        text2 = "mm"
        self.comboUnit.setCurrentIndex(u_idx) # default
        self.comboUnit.currentTextChanged.connect(lambda text2: self.on_value_changed("unit_mode", text2))


        # FGrid checkbox
        self.checkSlice = self.findChild(QCheckBox, "checkSlice")
        self.checkSlice.setChecked(params['slice'])  # make chaked
        self.checkSlice.stateChanged.connect(
            lambda state: self.on_value_changed("slice", state ==  Qt.Checked)
        )


        # FGrid checkbox
        self.chkAddGGide = self.findChild(QCheckBox, "chkAddGGide")
        self.chkAddGGide.setChecked(params['mod_grid_guide'])  # make chaked
        self.chkAddGGide.stateChanged.connect(
            lambda state: self.on_value_changed("mod_grid_guide", state ==  Qt.Checked)
        )




        # Text capacity checkbox
        self.chkTxtCapa = self.findChild(QCheckBox, "chkTxtCapa")
        self.chkTxtCapa.setChecked(params['txt_capa'])  # make chaked
        self.chkTxtCapa.stateChanged.connect(
            lambda state: self.on_value_changed("txt_capa", state ==  Qt.Checked)
        )
        self.chkTxtCapa.setToolTip("Display the estimated max text per frame (Active only if rows or columns are not divided)")

        # Rounded Corner checkbox
        self.chkRoundedCorners = self.findChild(QCheckBox, "chkRoundedCorners")
        self.chkRoundedCorners.setChecked(params['rounded_corners'])  # make chaked
        self.chkRoundedCorners.stateChanged.connect(
            lambda state: self.on_value_changed("rounded_corners", state ==  Qt.Checked)
        )
        self.chkTxtCapa.setToolTip("It rounds the corners of the grid units.")

        # Roundness
        self.Roundness = self.findChild(QSpinBox, "Roundness")
        self.Roundness.setSingleStep(1)
        self.Roundness.setRange(0, 100)
        self.Roundness.setValue(int(params["roundness"]))
        self.Roundness.valueChanged.connect(lambda val: self.on_value_changed("roundness", val))
        self.Roundness.setFixedWidth(50) 

        # Ignore shape size (Free total size)
        self.chkIgnoreShape = self.findChild(QCheckBox, "chkIgnoreShape")
        self.chkIgnoreShape.setChecked(params['ignore_shape'])  # make chaked
        self.chkIgnoreShape.stateChanged.connect(
            lambda state: self.on_value_changed("ignore_shape", state ==  Qt.Checked)
        )
        self.chkIgnoreShape.stateChanged.connect(self.on_ignore_shape_size_changed)
        ignore_shape = params.get("ignore_shape", False)
        self.chkIgnoreShape.setChecked(ignore_shape)
        self.chkIgnoreShape.setToolTip("Allows you to manually set the total size, ignoring the original shape dimensions.")


        #Grid Slices
        self.vcol_split = self.findChild(QSpinBox, "vCols")
        self.vcol_split.setRange(1, 128)
        self.vcol_split.setValue(int(params["vcol_split"]))
        self.vcol_split.valueChanged.connect(lambda val: self.on_value_changed("vcol_split",val))
        self.vcol_split.setFixedWidth(60) 

        self.vrow_split = self.findChild(QSpinBox, "vRows")
        self.vrow_split.setRange(1, 128) 
        self.vrow_split.setValue(int(params["vrow_split"]))
        self.vrow_split.valueChanged.connect(lambda val: self.on_value_changed("vrow_split",val))
        self.vrow_split.setFixedWidth(60) 

        spinbox_map = {
            "vtotal_w": "vTotal_w",
            "vtotal_h": "vTotal_h",
            "vunit_w": "vUnit_w",
            "vunit_h": "vUnit_h",
            "vcol_spc": "vColspacing",
            "vrow_spc": "vRowspacing",

            "vtotal_w_mm": "vTotal_wMm",
            "vtotal_h_mm": "vTotal_hMm",
            "vunit_w_mm": "vUnit_wMm",
            "vunit_h_mm": "vUnit_hMm",
            "vcol_spc_mm": "vColspacingMm",
            "vrow_spc_mm": "vRowspacingMm",

            "vtotal_w_px": "vTotal_wPx",
            "vtotal_h_px": "vTotal_hPx",
            "vunit_w_px": "vUnit_wPx",
            "vunit_h_px": "vUnit_hPx",
            "vcol_spc_px": "vColspacingPx",
            "vrow_spc_px": "vRowspacingPx",

            "vtotal_w_inch": "vTotal_wInch",
            "vtotal_h_inch": "vTotal_hInch",
            "vunit_w_inch": "vUnit_wInch",
            "vunit_h_inch": "vUnit_hInch",
            "vcol_spc_inch": "vColspacingInch",
            "vrow_spc_inch": "vRowspacingInch"

        }
        
        for key, obj_name in spinbox_map.items():
            spinbox = self.findChild(QDoubleSpinBox, obj_name)
            if spinbox:
                spinbox.setDecimals(2)
                spinbox.setSingleStep(0.1)
                spinbox.setRange(0.00001, 10000.0)
                spinbox.setSuffix(" mm")
                spinbox.setValue(float(params[key]))
                spinbox.valueChanged.connect(partial(self.on_value_changed, key))
                spinbox.setFixedWidth(0)# default hidden
                setattr(self, key, spinbox)#Save to self as attribute


        self.init_display_fields()
        self.on_unit_mode_changed("mm")#default
        self.toggle_total_spinboxes(params['ignore_shape'])

        #debug
        """
        self.dbg_w = self.findChild(QDoubleSpinBox, "dbgWpad")
        self.dbg_w.setDecimals(5)
        self.dbg_w.setSingleStep(0.001)
        self.dbg_w.setRange(0.000, 1000.0)
        self.dbg_w.setValue(float(params["dbg_wpad"]))
        self.dbg_w.valueChanged.connect(lambda val: self.on_value_changed("dbg_wpad", val))
        self.dbg_w.setFixedWidth(120)

        self.dbg_d = self.findChild(QDoubleSpinBox, "dbgDpad")
        self.dbg_d.setDecimals(5)
        self.dbg_d.setSingleStep(0.001)
        self.dbg_d.setRange(0.000, 1000.0)
        self.dbg_d.setValue(float(params["dbg_dpad"]))
        self.dbg_d.valueChanged.connect(lambda val: self.on_value_changed("dbg_dpad", val))
        self.dbg_d.setFixedWidth(120)
        """

        # Enable set
        self.vtotal_w.setEnabled(ignore_shape)
        self.vtotal_h.setEnabled(ignore_shape)

        # Wheel blocking
        self.wheel_blocker = WheelBlocker()
        for spin in [self.vrow_spc, self.vcol_spc, self.vrow_split, self.vcol_split,self.vtotal_w, self.vtotal_h, self.vunit_h,self.vunit_w]:
            spin.installEventFilter(self.wheel_blocker)

        # Buttons
        self.cancelButton = self.findChild(QPushButton, "cancelButton")
        self.okButton = self.findChild(QPushButton, "okButton")
        self.okButton.setStyleSheet(f"padding:3px;border: 3px solid {ac_color}; font-weight: bold; font-size: 14px;border-radius: 4px;")


        # Info checkbox
        self.checkInfo = self.findChild(QCheckBox, "checkInfo")
        self.checkInfo.setChecked(params['info'])  # make chaked
        self.checkInfo.stateChanged.connect(
            lambda state: self.on_value_changed("info", state ==  Qt.Checked)
        )

        # Dim
        self.checkDim = self.findChild(QCheckBox, "checkDim")
        self.checkDim.setChecked(params['dimension'])  # make chaked
        self.checkDim.stateChanged.connect(
            lambda state: self.on_value_changed("dimension", state ==  Qt.Checked)
        )
        # DimScale
        self.checkScale = self.findChild(QCheckBox, "checkScale")
        self.checkScale.setChecked(params['dim_scale'])  # make chaked
        self.checkScale.stateChanged.connect(
            lambda state: self.on_value_changed("dim_scale", state ==  Qt.Checked)
        )
        # DimScaleFactor
        self.dimScaleFactor = self.findChild(QSpinBox, "dimScaleFactor")
        self.dimScaleFactor.setSingleStep(1)
        self.dimScaleFactor.setRange(1, 10)
        self.dimScaleFactor.setPrefix("1/")
        self.dimScaleFactor.setValue(int(params["dim_scale_factor"]))
        self.dimScaleFactor.valueChanged.connect(lambda val: self.on_value_changed("dim_scale_factor", val))
        self.dimScaleFactor.setFixedWidth(50)

        # DimWidth
        self.checkDimW = self.findChild(QCheckBox, "checkDimW")
        self.checkDimW.setChecked(params['dim_w'])  # make chaked
        self.checkDimW.stateChanged.connect(
            lambda state: self.on_value_changed("dim_w", state ==  Qt.Checked)
        )
        # DimHeight
        self.checkDimH = self.findChild(QCheckBox, "checkDimH")
        self.checkDimH.setChecked(params['dim_h'])  # make chaked
        self.checkDimH.stateChanged.connect(
            lambda state: self.on_value_changed("dim_h", state ==  Qt.Checked)
        )


        # raddiobuttons set

        self.paper_dir_group = self.setup_radio_group(
            buttons={
                "vertical": self.radioVertical,
                "horizontal": self.radioHorizontal
            },
            default_key=params.get('size_dir',"vertical"),
            callback=lambda key: self.on_value_changed("size_dir", key)
        )

        
        # default
        self.radioDefault = self.findChild(QRadioButton, "radioDefault")
        self.radioJapanese = self.findChild(QRadioButton, "radioJapanese")
        
        self.crop_style_group = self.setup_radio_group(
            buttons={
                "default": self.radioDefault,
                "jp_trim": self.radioJapanese
            },
            default_key=params.get('crop_style',"default"),
            callback=lambda key: self.on_value_changed("crop_style", key)
        )





        # connect
        self.cancelButton.clicked.connect(self.cancel_dialog)
        self.okButton.clicked.connect(self.ok_dialog)

        # Paramater initialize
        # self.preview_state = params.copy() 
        for key, value in params.items():
            self.preview_state.set(key, value, emit_signal=False)
        # self.preview_state.stateChanged.connect(self.on_state_changed)
        self.preview_state.stateChanged.connect(self.update_ui_from_state)


        self.initialized = False
        self.setMaximumWidth(600)
        self.resize(self.sizeHint())



    def on_ignore_shape_size_changed(self, state):
        checked = (state == Qt.Checked)
        self.preview_state["ignore_shape"] = checked
    
        self.vtotal_w.setEnabled(checked)
        self.vtotal_h.setEnabled(checked)

        if self.preview_state["vcol_split"]==1:
            self.vtotal_w.setEnabled(True)
        if self.preview_state["vrow_split"]==1:
            self.vtotal_h.setEnabled(True)

        tip = "Override by Size" if checked else "Override by shape size"
        self.chkIgnoreShape.setToolTip(tip)



    def update_from_script(self, new_value):
        blocker = QSignalBlocker(self.some_widget)  # Signal block temporary
        self.some_widget.setValue(new_value)        # GUI upadate 
        del blocker  


    def update_ui_from_state(self, key, value):
        col_count = self.vcol_split.value()
        row_count = self.vrow_split.value()
    
        disable_col_related = col_count <= 1
        disable_row_related = row_count <= 1
    
        # widgetgroup
        col_widgets = [
            "vcol_spc", "vunit_w", "vtotal_w",
            "vcol_spc_mm", "vunit_w_mm", "vtotal_w_mm",
            "vcol_spc_px", "vunit_w_px", "vtotal_w_px",
            "vcol_spc_inch", "vunit_w_inch", "vtotal_w_inch"
        ]
        row_widgets = [
            "vrow_spc", "vunit_h", "vtotal_h",
            "vrow_spc_mm", "vunit_h_mm", "vtotal_h_mm",
            "vrow_spc_px", "vunit_h_px", "vtotal_h_px",
            "vrow_spc_inch", "vunit_h_inch", "vtotal_h_inch"
        ]
        # enable/disable
        for name in col_widgets:
            widget = getattr(self, name, None)
            if widget:
                if name.startswith("vtotal") and col_count==1:widget.setEnabled(True);continue
                widget.setEnabled(not disable_col_related)
    
        for name in row_widgets:
            widget = getattr(self, name, None)
            if widget:
                if name.startswith("vtotal") and row_count==1:widget.setEnabled(True);continue
                widget.setEnabled(not disable_row_related)

    
        # spinbox_update
        widget = getattr(self, key, None)
        if widget:
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)




    def update_all_ui_from_state(params):
        all_keys = [
            "vunit_w", "vunit_w_mm", "vunit_w_px", "vunit_w_inch",
            "vunit_h", "vunit_h_mm", "vunit_h_px", "vunit_h_inch",
            "vcol_spc", "vcol_spc_mm", "vcol_spc_px", "vcol_spc_inch",
            "vrow_spc", "vrow_spc_mm", "vrow_spc_px", "vrow_spc_inch",
            "vtotal_w", "vtotal_w_mm", "vtotal_w_px", "vtotal_w_inch",
            "vtotal_h", "vtotal_h_mm", "vtotal_h_px", "vtotal_h_inch",
            "vcol_split", "vrow_split"
        ]
        for key in all_keys:
            if key in params:
                update_ui_from_state(key, params[key])





    def create_combobox_with_separators(self,combobox, items, separator_token="__sep__"):
        """
        Add item and separator to QComboBox 
        
        Parameters:
            combobox (QComboBox): combo box
            items (list): 
            separator_token (str): default = "__sep__"
        """
        combobox.clear()
        for item in items:
            if item == separator_token:
                combobox.insertSeparator(combobox.count())
            else:
                combobox.addItem(item)



    def ok_dialog(self):
        global params
        p = params['prefix']
        if self.preview_state['preview']==False:
            self.preview_state['preview']=True
            script_main.re_init(p)
            script_main.main(self.preview_state)
            script_main.determine(p)
        else:
            script_main.determine(p)
        self.initialized = False
        self.accept()

    # close button
    def cancel_dialog(self):
        global params
        # Remove group(s) matching "preview_group"
        script_main.re_init(params['prefix'])
        self.initialized = False
        script_main.deselectAll()# Avoid segfault 11 bug 
        self.reject()


    def showEvent(self, event):
        """ Run the function when the dialog is first shown """
        super().showEvent(event)
        if not self.initialized:
            script_main.main(self.preview_state) # auto 
            self.initialized = True  # Execute at once




    def on_value_changed(self, key, value):
        global params, sizes

        if value == "":
            print("no value")
            return


        # same state
        # print(f"Signal:::: {key} {value}")
        if self.preview_state.get(key) == value:return
        # print("Now change key:", key, "  and value:", value)# When exist an user interraction


        self.preview_state[key] = value
        # total size mode (ignore shape size,the size control from gui)

        if key == 'ignore_shape':
            self.toggle_total_spinboxes(self.preview_state['ignore_shape'])

        # tode: unit mode sync
        if key == 'unit_mode':
            new_unit = self.preview_state['unit_mode']
            print(f"GUI update unit changed:{new_unit}")
            old_unit = self.preview_state['unit_mode']
            self.preview_state['old_unit_mode'] = old_unit
            self.preview_state['unit_mode'] = new_unit

            self.on_unit_mode_changed(new_unit)

        unit_exe_suffix=None
        # Note:grid_size_mode at initial is must be "unit"
        # When ignore_shape is False, grid_size_mode is forcibly set to "total"
        if self.preview_state.get("ignore_shape") is False:
            # base_key = key.split("_")[0] if key.startswith("v") and "_" in key else key
            base_key = "_".join(key.split("_")[:2]) if key.startswith("v") and "_" in key else key

            # Get unit from vunit_w_mm  
            unit_exe_suffix = self.get_unit_suffix(key)
            # ddune
            if base_key in ("vunit_w", "vunit_h"):
                self.preview_state.set("grid_size_mode", "unit")
            elif base_key in ("vtotal_w", "vtotal_h"):
                self.preview_state.set("grid_size_mode", "total")
            elif base_key in ("vrow_spc", "vcol_spc"):
                self.preview_state.set("grid_size_mode", "space")

        #Only when ignore_shape is True, grid_size_mode can be changed by modifying unit or total size
        elif self.preview_state.get("ignore_shape") is True:
            # base_key = key.split("_")[0] if key.startswith("v") and "_" in key else key
            base_key = "_".join(key.split("_")[:2]) if key.startswith("v") and "_" in key else key

            # Get the unit suffix from vxxxx_x_mm -> _mm 
            unit_exe_suffix = self.get_unit_suffix(key)
            if base_key in ("vunit_w", "vunit_h"):
                self.preview_state.set("grid_size_mode", "unit")
            elif base_key in ("vtotal_w", "vtotal_h"):
                self.preview_state.set("grid_size_mode", "total")
            elif base_key in ("vrow_spc", "vcol_spc"):
                self.preview_state.set("grid_size_mode", "space")

        if unit_exe_suffix is not None:
            base_key = "_".join(key.split("_")[:2])  #   vunit_w_px → vunit_w
            user_unit_value = self.preview_state.get(key)
            if user_unit_value in ("", None):
                return
        
            converted_value = self.uconv(user_unit_value, from_unit=unit_exe_suffix, to_unit="mm")

            #print("Argument:::",base_key,converted_value)
            self.preview_state[base_key] = converted_value
        
            # Switch to each mode 
            if base_key in ("vunit_w", "vunit_h"):
                self.preview_state["grid_size_mode"] = "unit"
            elif base_key in ("vtotal_w", "vtotal_h"):
                self.preview_state["grid_size_mode"] = "total"
            elif base_key in ("vcol_spc", "vrow_spc"):
                self.preview_state["grid_size_mode"] = "space"

            vt_h = self.preview_state["vtotal_h"]
            vt_w = self.preview_state["vtotal_w"]
            script_main.update_grid_layout(self.preview_state, vt_w, vt_h)


        # Preview ON
        if self.preview_state.get('preview', False):
            self.run_preview()
        else:
            prefix = self.preview_state.get('prefix', 'preview_')
            script_main.re_init(prefix)


    def get_unit_suffix(self,key):
        # Get unit suffix , for example _mm of vunit_w_mm  
        unit = None
        parts = key.split("_")
        if key.startswith("v") and len(parts) >= 3:
            unit = parts[-1]
            #print(f"signal emit:{key} and {unit}")
        return unit




    def changeEvent(self, event):
        global params,ac_color,is_dark
        if event.type() == QEvent.ActivationChange:
            if self.isActiveWindow() and not getattr(self, "_preview_updated", False):
                self._preview_updated = True
    
                if self.preview_state.get('preview', False):
                    self.run_preview()
            else:
                self._preview_updated = False


        if self.isActiveWindow():
            is_dark = is_ui_color_dark(self)
            ac_color = "#CCCCCC" if is_dark== True else "#111111"

        super().changeEvent(event)
    

    def get_all_info(self):
        ab = []

        all_list = self.collect_presets()
        
        for name in all_list:
            #print("Item:",name)
            if name == "__sep__":ab.append({'name': "__sep__" });continue

            dim = script_main.get_size(name, "vertical")
            dim['name'] = name
            ab.append(dim)

        self.print_all_size(ab)




    def run_preview(self):
        # Preview condition

        prefix = self.preview_state.get('prefix', 'preview_')
        script_main.re_init(prefix)
        script_main.main(self.preview_state)
        script_main.re_z_index(prefix, 9999)

    # ----------------
    # Utility functions
    # ----------------

    def toggle_total_spinboxes(self, enabled: bool):
        base_keys = ["vtotal_w", "vtotal_h"]
        suffixes = ["", "_mm", "_px", "_inch"]
    
        for base_key in base_keys:
            for suffix in suffixes:
                key = base_key + suffix  # For example vtotal_w_mm
    
                spinbox = self.findChild(QDoubleSpinBox, key)
                if spinbox:
                    spinbox.setEnabled(enabled)




    # This function only hide un-nessesary interface, no re-calculation 
    def on_unit_mode_changed(self, new_unit):
        global params
        #print(f"UnitChange old   -> new {new_unit}")
    
        base_keys = ["vunit_w", "vunit_h", "vcol_spc", "vrow_spc", "vtotal_w", "vtotal_h"]
        units = ["mm", "px", "inch"]
    
        for base_key in base_keys:
            for unit in units:
                widget_name = f"{base_key}_{unit}"
                widget = getattr(self, widget_name, None)
                if widget:
                    if unit == new_unit:
                        widget.setFixedWidth(100)# visible
                    else:
                        #print(f"set Disabled:::{widget_name}")
                        widget.setFixedWidth(0)# hidden



    # Convert a value by other units
    def uconv(self,value,from_unit="mm",to_unit="mm"):
        if from_unit == to_unit:
            return value  # same unit
        ret=0
        if from_unit == "mm":
            mm=value
            if to_unit == "inch":ret = script_main.conv_mm_to_inch(mm)   # return inch
            if to_unit == "px"  :ret = script_main.conv_mm_to_px(mm)     # return px
        if from_unit == "inch":
            inch=value
            if to_unit == "mm":ret = script_main.conv_inch_to_mm(inch) # return mm
            if to_unit == "px":ret = script_main.conv_inch_to_px(inch) # return px
        if from_unit == "px":
            px=value
            if to_unit == "mm"  :ret = script_main.conv_px_to_mm(px)     # return mm
            if to_unit == "inch":ret = script_main.conv_px_to_inch(px)   # return inch

        return ret

    # refresh_ui
    def init_display_fields(self):
        keys = [
            'vunit_w', 'vunit_h',
            'vcol_spc', 'vrow_spc',
            'vtotal_w', 'vtotal_h'
        ]
    
        for key in keys:
            mm = self.preview_state.get(key, 0.0)
    
            # Upadte for the value of display  
            self.preview_state[f'{key}_mm'] = mm
            self.preview_state[f'{key}_inch'] = script_main.conv_mm_to_inch(mm)
            self.preview_state[f'{key}_px'] = script_main.conv_mm_to_px(mm)
    
            # If UI element exist,update it
            for unit in ['mm', 'inch', 'px']:
                ui_key = f'{key}_{unit}'
                if hasattr(self, ui_key):
                    getattr(self, ui_key).setValue(self.preview_state[ui_key])
                    getattr(self, ui_key).setSuffix(" " + unit)
                    if unit != "mm":
                        getattr(self, ui_key).setEnabled(False)


    # ----------------
    # Radio functions
    # ----------------
    def setup_radio_group(self,buttons: dict, default_key: str, callback):
        """
        buttons: {key: QRadioButton}  
        default_key: Default key
        callback: Callback funtion(arg:key)
        """
        group = QButtonGroup()
        for key, btn in buttons.items():
            group.addButton(btn)
            btn.blockSignals(True)  # for  Initialize
    
        # Default 
        if default_key in buttons:
            buttons[default_key].setChecked(True)
    
        for btn in buttons.values():
            btn.blockSignals(False)
    
        # connect signal(return key of the choosed button )
        def on_clicked(button):
            for key, b in buttons.items():
                if b == button:
                    callback(key)
                    break
    
        group.buttonClicked.connect(on_clicked)
        return group

    # ----------------
    # Menu functions
    # ----------------
    def onPresetChanged(self, text):
        if text in self.preset_papers:
            self.preview_state['preset'] = text
            self.updateSizeOptions(text)

    def updateSizeOptions(self, preset_name):
        self.comboSize.clear()

        if preset_name=="All":
            size_list = self.collect_presets()
        else:
            size_list = self.preset_papers.get(preset_name, [])

        self.create_combobox_with_separators(self.comboSize, size_list)


    def collect_presets(self):
        global sizes,fixed_sizes
        sizes_list = list(sizes.keys())

        combined_list = fixed_sizes + sizes_list
        return combined_list




    # ----------------
    # Print functions
    # ----------------
    def print_all_size(self,array):
        print("== All size  ==")
        slog=[]
        for a in array:
            name = a['name']
            if name == "__sep__":continue
            width = round(a['width']*0.3528,2)
            height = round(a['height']*0.3528)
            print(f" {name}: ({width}mm x {height}mm)\n")
            slog.append(f" {name}: ({width}mm x {height}mm)")


        print("=============")
        # call_log window
        if self.log_window is None:
            self.add_log_message("\n".join(slog))

    # ----------------
    # log
    # ----------------
    def show_log_window(self):
        if self.log_window is None:
            self.log_window = LogWindow(self)

        self.log_window.show()
        self.log_window.raise_()  # bring to front
        self.log_window.activateWindow()

    def add_log_message(self, message):
        if self.log_window is None:
            self.show_log_window()
        self.log_window.clear_log()
        self.log_window.append_log(message)


class PreviewState(QObject):
    stateChanged = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self._data = {}

    def set(self, key, value, emit_signal=True):
        if self._data.get(key) == value:
            return
        self._data[key] = value
        if emit_signal:
            self.stateChanged.emit(key, value)

    def __setitem__(self, key, value):
        self.set(key, value)

    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def __getitem__(self, key):
        return self._data[key]  # May raise KeyError


    def to_dict(self):
        return self._data.copy()

    def from_dict(self, data: dict, emit_signal=False):
        for key, value in data.items():
            self.set(key, value, emit_signal=emit_signal)






# Run this command directly
def run_direct(self):
    global params
    params['mode'] = "direct"
    script_main.main(params)
    script_main.determine(params['prefix'])

def is_ui_color_dark(self):
    palette = QApplication.palette()
    bg_color = palette.color(QPalette.Window)

    brightness = (bg_color.red() * 299 + bg_color.green() * 587 + bg_color.blue() * 114) / 1000
    
    if brightness < 128:
        print("Dark theme detected");return True
    else:
        print("Light theme detected");return False


class vector_guide_marks(Extension):

    def __init__(self, parent):
        # This is initialising the parent, always important when subclassing.
        super().__init__(parent)
        self.dialog = create_VectorGuidMarksDialog()
        script_main.parent_dialog = self.dialog


    def setup(self):
        #This runs only once when app is installed
        pass

    def createActions(self, window):
        action = window.createAction("create many kinds of marks on the vector shapes", "Vector Guide Marks...", "tools/scripts")
        action.triggered.connect(self.dialog.show)


# And add the extension to Krita's list of extensions:
Krita.instance().addExtension(vector_guide_marks(Krita.instance())) 
