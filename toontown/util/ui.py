from direct.gui import DirectGuiGlobals
from direct.gui.DirectScrolledList import DirectScrolledList


def make_dsl_scrollable(dsl: DirectScrolledList):
    affected_ui = [dsl.itemFrame, dsl]
    for item in dsl['items']:
        if not isinstance(item, str):
            affected_ui.append(item)

    for ui in affected_ui:
        ui.bind(DirectGuiGlobals.WHEELUP, lambda *_: dsl.scrollTo(dsl.index - 1))
        ui.bind(DirectGuiGlobals.WHEELDOWN, lambda *_: dsl.scrollTo(dsl.index + 1))
