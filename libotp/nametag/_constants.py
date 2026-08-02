CFSpeech = 1
CFThought = 2
CFQuicktalker = 4
CFTimeout = 8
CFPageButton = 16
CFQuitButton = 32
CFReversed = 64
CFSndOpenchat = 128
CFNoQuitButton = 256

# Some nametag modules expect PGButton to be in this namespace via
# `from ._constants import *`.
from direct.gui.DirectGuiGlobals import PGButton
