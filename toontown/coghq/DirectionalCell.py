from direct.directnotify import DirectNotifyGlobal

from . import ActiveCell


class DirectionalCell(ActiveCell.ActiveCell):
    notify = DirectNotifyGlobal.directNotify.newCategory('DirectionalCell')

    def __init__(self, cr):
        ActiveCell.ActiveCell.__init__(self, cr)
