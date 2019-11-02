from pandac.PandaModules import *
from direct.gui.DirectGui import *
from direct.task import Task
from SCConstants import *
from direct.interval.IntervalGlobal import *
from SCObject import SCObject
from direct.showbase.PythonUtil import makeTuple
import types

class SCMenu(SCObject, NodePath):
    config = getConfigShowbase()
    SpeedChatRolloverTolerance = config.GetFloat('speedchat-rollover-tolerance', 0.08)
    WantFade = config.GetBool('want-speedchat-fade', 0)
    FadeDuration = config.GetFloat('speedchat-fade-duration', 0.2)
    SerialNum = 0
    BackgroundModelName = None
    GuiModelName = None

    def __init__(self, holder = None):
        SCObject.__init__(self)
        self.SerialNum = SCMenu.SerialNum
        SCMenu.SerialNum += 1
        node = hidden.attachNewNode('SCMenu%s' % self.SerialNum)
        NodePath.__init__(self, node)
        self.setHolder(holder)
        self.FinalizeTaskName = 'SCMenu%s_Finalize' % self.SerialNum
        self.ActiveMemberSwitchTaskName = 'SCMenu%s_SwitchActiveMember' % self.SerialNum
        self.bg = loader.loadModel(self.BackgroundModelName)

        def findNodes(names, model = self.bg):
            results = []
            for name in names:
                for nm in makeTuple(name):
                    node = model.find('**/%s' % nm)
                    if not node.isEmpty():
                        results.append(node)
                        break

            return results

        self.bgTop, self.bgBottom, self.bgLeft, self.bgRight, self.bgMiddle, self.bgTopLeft, self.bgBottomLeft, self.bgTopRight, self.bgBottomRight = findNodes([('top', 'top1'),
         'bottom',
         'left',
         'right',
         'middle',
         'topLeft',
         'bottomLeft',
         'topRight',
         'bottomRight'])
        self.bg.reparentTo(self, -1)
        self.__members = []
        self.activeMember = None
        self.activeCandidate = None
        self.fadeIval = None
        self.width = 1
        self.inFinalize = 0
        return

    def destroy(self):
        self.stopFade()
        SCObject.destroy(self)
        del self.bgTop
        del self.bgBottom
        del self.bgLeft
        del self.bgRight
        del self.bgMiddle
        del self.bgBottomLeft
        del self.bgTopRight
        del self.bgBottomRight
        self.bg.removeNode()
        del self.bg
        self.holder = None
        for member in self.__members:
            member.destroy()

        del self.__members
        self.removeNode()
        taskMgr.remove(self.FinalizeTaskName)
        taskMgr.remove(self.ActiveMemberSwitchTaskName)
        return

    def clearMenu(self):
        while len(self):
            item = self[0]
            del self[0]
            item.destroy()

    def rebuildFromStructure(self, structure, title = None):
        self.clearMenu()
        if title:
            holder = self.getHolder()
            if holder:
                holder.setTitle(title)
        self.appendFromStructure(structure)

    def appendFromStructure(self, structure):
        from SpeedChatTypes import SCMenuHolder, SCStaticTextTerminal, SCGMTextTerminal
        from otp.otpbase import OTPLocalizer

        def addChildren(menu, childList):
            for child in childList:
                emote = None
                if type(child) == type({}):
                    item = child.keys()[0]
                    emote = child[item]
                    child = item
                if type(child) == type(0):
                    terminal = SCStaticTextTerminal(child)
                    if emote is not None:
                        terminal.setLinkedEmote(emote)
                    menu.append(terminal)
                elif type(child) == type([]):
                    if type(child[0]) == type(''):
                        holderTitle = child[0]
                        subMenu = SCMenu()
                        subMenuChildren = child[1:]
                    else:
                        menuType, holderTitle = child[0], child[1]
                        subMenu = menuType()
                        subMenuChildren = child[2:]
                    if emote:
                        print 'warning: tried to link emote %s to a menu holder' % emote
                    holder = SCMenuHolder(holderTitle, menu=subMenu)
                    menu.append(holder)
                    addChildren(subMenu, subMenuChildren)
                elif type(child) == type('') and child[:2] == 'gm':
                    terminal = SCGMTextTerminal(child)
                    menu.append(terminal)
                else:
                    raise 'error parsing speedchat structure. invalid child: %s' % child

            return

        addChildren(self, structure)
        addChildren = None
        return

    def fadeFunc(self, t):
        cs = self.getColorScale()
        self.setColorScale(cs[0], cs[1], cs[2], t)

    def stopFade(self):
        if self.fadeIval is not None:
            self.fadeIval.pause()
            self.fadeIval = None
        return

    def enterVisible(self):
        SCObject.enterVisible(self)
        self.privScheduleFinalize()
        for member in self:
            if member.isViewable():
                if not member.isVisible():
                    member.enterVisible()

        self.childHasFaded = 0
        alreadyFaded = 0
        parentMenu = None
        if self.holder is not None:
            if self.holder.parentMenu is not None:
                parentMenu = self.holder.parentMenu
                alreadyFaded = parentMenu.childHasFaded
        if SCMenu.WantFade:
            if alreadyFaded:
                self.fadeFunc(1.0)
            else:
                self.stopFade()
                self.fadeIval = LerpFunctionInterval(self.fadeFunc, fromData=0.0, toData=1.0, duration=SCMenu.FadeDuration)
                self.fadeIval.play()
                if parentMenu is not None:
                    parentMenu.childHasFaded = 1
        return

    def exitVisible(self):
        SCObject.exitVisible(self)
        self.stopFade()
        self.privCancelFinalize()
        self.__cancelActiveMemberSwitch()
        self.__setActiveMember(None)
        for member in self:
            if member.isVisible():
                member.exitVisible()

        return

    def setHolder(self, holder):
        self.holder = holder

    def getHolder(self):
        return self.holder

    def isTopLevel(self):
        return self.holder == None

    def memberSelected(self, member):
        self.__cancelActiveMemberSwitch()
        self.__setActiveMember(member)

    def __setActiveMember(self, member):
        if self.activeMember is member:
            return
        if self.activeMember is not None:
            self.activeMember.exitActive()
        self.activeMember = member
        if self.activeMember is not None:
            self.activeMember.reparentTo(self)
            self.activeMember.enterActive()
        return

    def memberGainedInputFocus(self, member):
        self.__cancelActiveMemberSwitch()
        if member is self.activeMember:
            return
        if self.activeMember is None or SCMenu.SpeedChatRolloverTolerance == 0 or member.posInParentMenu < self.activeMember.posInParentMenu:
            self.__setActiveMember(member)
        else:

            def doActiveMemberSwitch(task, self = self, member = member):
                self.activeCandidate = None
                self.__setActiveMember(member)
                return Task.done

            minFrameRate = 1.0 / SCMenu.SpeedChatRolloverTolerance
            if globalClock.getAverageFrameRate() > minFrameRate:
                taskMgr.doMethodLater(SCMenu.SpeedChatRolloverTolerance, doActiveMemberSwitch, self.ActiveMemberSwitchTaskName)
                self.activeCandidate = member
            else:
                self.__setActiveMember(member)
        return

    def __cancelActiveMemberSwitch(self):
        taskMgr.remove(self.ActiveMemberSwitchTaskName)
        self.activeCandidate = None
        return

    def memberLostInputFocus(self, member):
        if member is self.activeCandidate:
            self.__cancelActiveMemberSwitch()
        if member is not self.activeMember:
            pass
        elif not member.hasStickyFocus():
            self.__setActiveMember(None)
        return

    def memberViewabilityChanged(self, member):
        self.invalidate()

    def invalidate(self):
        SCObject.invalidate(self)
        if self.isVisible():
            self.privScheduleFinalize()

    def privScheduleFinalize(self):

        def finalizeMenu(task, self = self):
            self.finalize()
            return Task.done

        taskMgr.remove(self.FinalizeTaskName)
        taskMgr.add(finalizeMenu, self.FinalizeTaskName, priority=SCMenuFinalizePriority)

    def privCancelFinalize(self):
        taskMgr.remove(self.FinalizeTaskName)

    def isFinalizing(self):
        return self.inFinalize

    def finalize(self):
        if not self.isDirty():
            return
        self.inFinalize = 1
        SCObject.finalize(self)
        visibleMembers = []
        for member in self:
            if member.isViewable():
                visibleMembers.append(member)
                member.reparentTo(self)
            else:
                member.reparentTo(hidden)
                if self.activeMember is member:
                    self.__setActiveMember(None)

        maxWidth = 0.0
        maxHeight = 0.0
        for member in visibleMembers:
            width, height = member.getMinDimensions()
            maxWidth = max(maxWidth, width)
            maxHeight = max(maxHeight, height)

        holder = self.getHolder()
        if holder is not None:
            widthToCover = holder.getMinSubmenuWidth()
            maxWidth = max(maxWidth, widthToCover)
        memberWidth, memberHeight = maxWidth, maxHeight
        self.width = maxWidth
        for i in xrange(len(visibleMembers)):
            member = visibleMembers[i]
            member.setPos(0, 0, -i * maxHeight)
            member.setDimensions(memberWidth, memberHeight)
            member.finalize()

        if len(visibleMembers) > 0:
            z1 = visibleMembers[0].getZ(aspect2d)
            visibleMembers[0].setZ(-maxHeight)
            z2 = visibleMembers[0].getZ(aspect2d)
            visibleMembers[0].setZ(0)
            actualHeight = (z2 - z1) * len(visibleMembers)
            bottomZ = self.getZ(aspect2d) + actualHeight
            if bottomZ < -1.0:
                overlap = bottomZ - -1.0
                self.setZ(aspect2d, self.getZ(aspect2d) - overlap)
            if self.getZ(aspect2d) > 1.0:
                self.setZ(aspect2d, 1.0)
        sX = memberWidth
        sZ = memberHeight * len(visibleMembers)
        self.bgMiddle.setScale(sX, 1, sZ)
        self.bgTop.setScale(sX, 1, 1)
        self.bgBottom.setScale(sX, 1, 1)
        self.bgLeft.setScale(1, 1, sZ)
        self.bgRight.setScale(1, 1, sZ)
        self.bgBottomLeft.setZ(-sZ)
        self.bgBottom.setZ(-sZ)
        self.bgTopRight.setX(sX)
        self.bgRight.setX(sX)
        self.bgBottomRight.setX(sX)
        self.bgBottomRight.setZ(-sZ)
        sB = 0.15
        self.bgTopLeft.setSx(aspect2d, sB)
        self.bgTopLeft.setSz(aspect2d, sB)
        self.bgBottomRight.setSx(aspect2d, sB)
        self.bgBottomRight.setSz(aspect2d, sB)
        self.bgBottomLeft.setSx(aspect2d, sB)
        self.bgBottomLeft.setSz(aspect2d, sB)
        self.bgTopRight.setSx(aspect2d, sB)
        self.bgTopRight.setSz(aspect2d, sB)
        self.bgTop.setSz(aspect2d, sB)
        self.bgBottom.setSz(aspect2d, sB)
        self.bgLeft.setSx(aspect2d, sB)
        self.bgRight.setSx(aspect2d, sB)
        r, g, b = self.getColorScheme().getFrameColor()
        a = self.getColorScheme().getAlpha()
        self.bg.setColorScale(r, g, b, a)
        if self.activeMember is not None:
            self.activeMember.reparentTo(self)
        self.validate()
        self.inFinalize = 0
        return

    def append(self, element):
        if isinstance(self.__members, types.TupleType):
            self.__members = list(self.__members)
        self.__members.append(element)
        self.privMemberListChanged(added=[element])

    def extend(self, elements):
        self += elements

    def index(self, element):
        return self.__members.index(element)

    def __len__(self):
        return len(self.__members)

    def __getitem__(self, index):
        return self.__members[index]

    def __setitem__(self, index, value):
        if isinstance(self.__members, types.TupleType):
            self.__members = list(self.__members)
        removedMember = self.__members[index]
        self.__members[index] = value
        self.privMemberListChanged(added=[value], removed=[removedMember])

    def __delitem__(self, index):
        if isinstance(self.__members, types.TupleType):
            self.__members = list(self.__members)
        removedMember = self.__members[index]
        del self.__members[index]
        self.privMemberListChanged(removed=[removedMember])

    def __getslice__(self, i, j):
        if isinstance(self.__members, types.TupleType):
            self.__members = list(self.__members)
        return self.__members[i:j]

    def __setslice__(self, i, j, s):
        if isinstance(self.__members, types.TupleType):
            self.__members = list(self.__members)
        removedMembers = self.__members[i:j]
        self.__members[i:j] = list(s)
        self.privMemberListChanged(added=list(s), removed=removedMembers)

    def __delslice__(self, i, j):
        if isinstance(self.__members, types.TupleType):
            self.__members = list(self.__members)
        removedMembers = self.__members[i:j]
        del self.__members[i:j]
        self.privMemberListChanged(removed=removedMembers)

    def __iadd__(self, other):
        if isinstance(self.__members, types.TupleType):
            self.__members = list(self.__members)
        if isinstance(other, SCMenu):
            otherMenu = other
            other = otherMenu.__members
            del otherMenu[:]
        self.__members += list(other)
        self.privMemberListChanged(added=list(other))
        return self

    def privMemberListChanged(self, added = None, removed = None):
        if removed is not None:
            for element in removed:
                if element is self.activeMember:
                    self.__setActiveMember(None)
                if element.getParentMenu() is self:
                    if element.isVisible():
                        element.exitVisible()
                    element.setParentMenu(None)
                    element.reparentTo(hidden)

        if added is not None:
            for element in added:
                self.privAdoptSCObject(element)
                element.setParentMenu(self)

        if self.holder is not None:
            self.holder.updateViewability()
        for i in range(len(self.__members)):
            self.__members[i].posInParentMenu = i

        self.invalidate()
        return

    def privSetSettingsRef(self, settingsRef):
        SCObject.privSetSettingsRef(self, settingsRef)
        for member in self:
            member.privSetSettingsRef(settingsRef)

    def invalidateAll(self):
        SCObject.invalidateAll(self)
        for member in self:
            member.invalidateAll()

    def finalizeAll(self):
        SCObject.finalizeAll(self)
        for member in self:
            member.finalizeAll()

    def getWidth(self):
        return self.width

    def __str__(self):
        return '%s: menu%s' % (self.__class__.__name__, self.SerialNum)
