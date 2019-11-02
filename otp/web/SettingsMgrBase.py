from direct.directnotify.DirectNotifyGlobal import directNotify

class SettingsMgrBase:
    notify = directNotify.newCategory('SettingsMgrBase')

    def announceGenerate(self):
        self._settings = {}
        self._originalValueReprs = {}
        self._currentValueReprs = {}
        self._initSettings()

    def delete(self):
        del self._settings

    def _initSettings(self):
        pass

    def _iterSettingNames(self):
        for name in self._settings.iterkeys():
            yield name

    def _addSettings(self, *settings):
        for setting in settings:
            self._addSetting(setting)

    def _addSetting(self, setting):
        name = setting.getName()
        if name in self._settings:
            self.notify.error('duplicate setting "%s"' % name)
        self._settings[name] = setting
        self._originalValueReprs[name] = repr(setting.getValue())
        self._currentValueReprs[name] = repr(setting.getValue())

    def _getOriginalValueRepr(self, settingName):
        return self._originalValueReprs.get(settingName)

    def _getCurrentValueRepr(self, settingName):
        return self._currentValueReprs.get(settingName)

    def _removeSetting(self, setting):
        del self._settings[setting.getName()]
        del self._originalValueReprs[setting.getName()]
        del self._currentValueReprs[setting.getName()]

    def _getSetting(self, settingName):
        return self._settings[settingName]

    def _isSettingModified(self, settingName):
        return self._getOriginalValueRepr(settingName) != self._getCurrentValueRepr(settingName)

    def _changeSetting(self, settingName, valueStr):
        try:
            val = eval(valueStr)
        except:
            self.notify.warning('error evaling "%s" for setting "%s"' % (valueStr, settingName))
            return

        try:
            setting = self._getSetting(settingName)
        except:
            self.notify.warning('unknown setting %s' % settingName)
            return

        setting.setValue(val)
        self._currentValueReprs[settingName] = valueStr
