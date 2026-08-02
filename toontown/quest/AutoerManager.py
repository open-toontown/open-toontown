"""Loads client autoer bundle and provides global stop (sticker book + backslash)."""

import importlib.util
import os
import traceback

from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from direct.task.TaskManagerGlobal import taskMgr

from toontown.quest import task_autoer_globals as TAG
from toontown.toonbase import ToontownBattleGlobals

notify = DirectNotifyGlobal.directNotify.newCategory('AutoerManager')

_bundleModule = None


def _logAutoerException(context, exc):
    """Log full traceback for autoer failures (notify + stdout)."""
    tb = traceback.format_exc()
    notify.warning('%s: %s\n%s' % (context, exc, tb))
    try:
        print('[AutoerManager] %s: %s' % (context, exc))
        print(tb)
    except Exception:
        pass
_emergencyListener = None

# Pending async close of sticker book before task autoer starts (see startTaskAutomation).
_TASK_AUTOER_BOOK_CLOSE = 'autoerTaskAutomationBookClose'


def isBundleLoaded():
    return _bundleModule is not None


def getBundleModule():
    return _bundleModule


def _bundlePath():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(root, 'autoers', 'TaskAutoer full source.py')


def loadAutoerBundle():
    global _bundleModule
    if _bundleModule is not None:
        notify.info('Autoer bundle already loaded.')
        return _bundleModule
    path = _bundlePath()
    if not os.path.isfile(path):
        notify.warning('Autoer bundle not found at %s' % path)
        return None
    name = 'ttbtn_autoer_bundle_%s' % hash(path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _bundleModule = mod
    notify.info('Loaded autoer bundle from %s' % path)
    return mod


def stopAllAutoers():
    m = _bundleModule
    from toontown.quest.TaskAutoer import revert_task_autoer

    if m is not None:
        try:
            if getattr(m, 'buildingAutoer', None):
                m.buildingAutoer.stop()
                m.buildingAutoer.revert()
        except Exception as e:
            notify.warning('buildingAutoer stop: %s' % e)

        try:
            if getattr(m, 'gagTrainer', None):
                m.gagTrainer.stop()
                from toontown.battle import BattlePlace
                from toontown.battle import DistributedBattle
                from toontown.suit import DistributedSuit
                from toontown.toon import HealthForceAcknowledge
                DistributedBattle.DistributedBattle.enterReward = m.GagTrainer.oldEnterReward
                DistributedBattle.DistributedBattle.enterFaceOff = m.GagTrainer.oldEnterFaceOff
                DistributedSuit.DistributedSuit.denyBattle = m.GagTrainer.oldDenyBattle
                HealthForceAcknowledge.HealthForceAcknowledge.enter = m.GagTrainer.oldEnterHealth
                BattlePlace.BattlePlace.exitTeleportIn = m.GagTrainer.oldBattlePlaceTeleportIn
                try:
                    rs = m.gagTrainer.restock
                    rf = getattr(rs, 'revertFunctions', None)
                    if callable(rf):
                        rf()
                except Exception as e:
                    notify.warning('gagTrainer restock.revertFunctions: %s' % e)
        except Exception as e:
            notify.warning('gagTrainer stop: %s' % e)

        for name in ('vpMaxer', 'cfoMaxer', 'ceoMaxer'):
            try:
                mx = getattr(m, name, None)
                if mx is not None and hasattr(mx, 'revert'):
                    mx.revert()
            except Exception as e:
                notify.warning('%s revert: %s' % (name, e))

    try:
        cj = TAG.cjMaxer
        if cj is not None and hasattr(cj, 'revert'):
            cj.revert()
    except Exception as e:
        notify.warning('cjMaxer revert: %s' % e)

    try:
        revert_task_autoer()
    except Exception as e:
        notify.warning('taskAutoer revert: %s' % e)

    for name in ('buildingAutoer', 'gagTrainer', 'vpMaxer', 'cfoMaxer', 'cjMaxer', 'ceoMaxer'):
        try:
            setattr(TAG, name, None)
        except Exception:
            pass

    ToontownBattleGlobals.SkipMovie = 0

    if m is not None:
        try:
            m.taskAutoer = None
        except Exception:
            pass

    try:
        base.localAvatar.setSystemMessage(0, 'All autoers stopped.')
    except Exception:
        pass

    try:
        taskMgr.remove(_TASK_AUTOER_BOOK_CLOSE)
    except Exception:
        pass

    return True


def _runStartTaskAutomationCore():
    """Load bundle, bootstrap, and run first check (call when safe to run logic)."""
    if not loadAutoerBundle():
        try:
            base.localAvatar.setSystemMessage(0, 'Autoer bundle missing. Add autoers/TaskAutoer full source.py')
        except Exception:
            pass
        return False
    m = _bundleModule
    try:
        from toontown.quest.TaskAutoer import bootstrap_task_autoer
        ta = bootstrap_task_autoer()
        m.taskAutoer = ta
        ta.checkWhatToDo()
    except Exception as e:
        _logAutoerException('startTaskAutomation', e)
        try:
            detail = traceback.format_exc()
            msg = 'Could not start task autoer: %s\n%s' % (e, detail)
            if len(msg) > 2000:
                msg = msg[:2000] + '\n... (truncated)'
            base.localAvatar.setSystemMessage(0, msg)
        except Exception:
            pass
        return False
    return True


def _taskAutoerBookCloseSequence(task):
    """
    Close the sticker book the same way the player would (closeBook -> bookDone ->
    CloseBook anim -> walk). Do not fsm.request('walk') synchronously: if OpenBook's
    callback has not run yet, enterStickerBookGUI can fire after we leave stickerBook
    and reopen the book (render hidden, mouse off) while in walk — total control loss.
    """
    try:
        place = base.cr.playGame.getPlace()
        if place is None or place.getState() != 'stickerBook':
            taskMgr.remove(_TASK_AUTOER_BOOK_CLOSE)
            _runStartTaskAutomationCore()
            return task.done
        book = base.localAvatar.book
        if not getattr(book, 'entered', 0):
            task.waitEnter = getattr(task, 'waitEnter', 0) + 1
            if task.waitEnter > 300:
                notify.warning('AutoerManager: book GUI never became active; starting task autoer')
                taskMgr.remove(_TASK_AUTOER_BOOK_CLOSE)
                _runStartTaskAutomationCore()
                return task.done
            return task.cont
        if not getattr(task, 'issuedClose', 0):
            book.closeBook()
            task.issuedClose = 1
        if place.getState() != 'stickerBook':
            taskMgr.remove(_TASK_AUTOER_BOOK_CLOSE)
            _runStartTaskAutomationCore()
            return task.done
        task.waitLeave = getattr(task, 'waitLeave', 0) + 1
        if task.waitLeave > 600:
            notify.warning('AutoerManager: timeout leaving stickerBook; starting task autoer')
            taskMgr.remove(_TASK_AUTOER_BOOK_CLOSE)
            _runStartTaskAutomationCore()
            return task.done
        return task.cont
    except Exception as e:
        notify.warning('_taskAutoerBookCloseSequence: %s' % e)
        try:
            taskMgr.remove(_TASK_AUTOER_BOOK_CLOSE)
        except Exception:
            pass
        _runStartTaskAutomationCore()
        return task.done


def startTaskAutomation():
    try:
        place = base.cr.playGame.getPlace()
        if place is not None and getattr(place, 'fsm', None) is not None:
            if place.getState() == 'stickerBook':
                taskMgr.remove(_TASK_AUTOER_BOOK_CLOSE)
                taskMgr.add(_taskAutoerBookCloseSequence, _TASK_AUTOER_BOOK_CLOSE)
                return True
    except Exception as e:
        notify.warning('startTaskAutomation (defer sticker book): %s' % e)
    return _runStartTaskAutomationCore()


class _EmergencyStopListener(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        for ev in ('backslash', 'raw-backslash'):
            self.accept(ev, self._onStop)
        try:
            self.accept('\\', self._onStop)
        except Exception:
            pass

    def _onStop(self):
        stopAllAutoers()

    def destroy(self):
        self.ignoreAll()


def attachEmergencyStopListener():
    global _emergencyListener
    if _emergencyListener is not None:
        return
    _emergencyListener = _EmergencyStopListener()


def detachEmergencyStopListener():
    global _emergencyListener
    if _emergencyListener is None:
        return
    _emergencyListener.destroy()
    _emergencyListener = None
