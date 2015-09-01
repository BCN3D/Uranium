# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSlot, QUrl

from UM.Application import Application
from UM.Qt.ListModel import ListModel
from UM.Settings.SettingOverrideDecorator import SettingOverrideDecorator

class SettingOverrideModel(ListModel):
    KeyRole = Qt.UserRole + 1
    LabelRole = Qt.UserRole + 2
    DescriptionRole = Qt.UserRole + 3
    ValueRole = Qt.UserRole + 4
    TypeRole = Qt.UserRole + 5
    UnitRole = Qt.UserRole + 6
    ValidRole = Qt.UserRole + 7

    def __init__(self, node, parent = None):
        super().__init__(parent)

        self._node = node
        self._node.decoratorsChanged.connect(self._onDecoratorsChanged)
        self._onDecoratorsChanged(None)

        self.addRoleName(self.KeyRole, "key")
        self.addRoleName(self.LabelRole, "label")
        self.addRoleName(self.DescriptionRole, "description")
        self.addRoleName(self.ValueRole,"value")
        self.addRoleName(self.TypeRole, "type")
        self.addRoleName(self.UnitRole, "unit")
        self.addRoleName(self.ValidRole, "valid")

    @pyqtSlot(str, "QVariant")
    def setSettingValue(self, key, value):
        if not self._decorator:
            return

        self._decorator.setSettingValue(key, value)

    def _onDecoratorsChanged(self, node):
        if not self._node.getDecorator(SettingOverrideDecorator):
            self.clear()
            return

        self._decorator = self._node.getDecorator(SettingOverrideDecorator)
        self._decorator.settingAdded.connect(self._onSettingsChanged)
        self._decorator.settingRemoved.connect(self._onSettingsChanged)
        self._decorator.settingChanged.connect(self._onSettingChanged)
        self._onSettingsChanged()

    def _onSettingsChanged(self):
        self.clear()

        for key, setting in self._decorator.getAllSettings().items():
            self.appendItem({
                "key": key,
                "label": setting.getLabel(),
                "description": setting.getDescription(),
                "value": setting.getValue(),
                "type": setting.getType(),
                "unit": setting.getUnit(),
                "valid": setting.validate()
            })

    def _onSettingChanged(self, setting):
        index = self.find("key", setting.getKey())
        if index != -1:
            self.setProperty(index, "value", setting.getValue())
            self.setProperty(index, "valid", setting.validate())