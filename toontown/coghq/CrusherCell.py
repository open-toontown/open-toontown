from direct.directnotify import DirectNotifyGlobal

from . import ActiveCell


class CrusherCell(ActiveCell.ActiveCell):
    notify = DirectNotifyGlobal.directNotify.newCategory('CrusherCell')

    def __init__(self, cr):
        ActiveCell.ActiveCell.__init__(self, cr)
