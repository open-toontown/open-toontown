from toontown.toonbase import ToontownGlobals

def calcPropType(node):
    propType = ToontownGlobals.AnimPropTypes.Unknown
    fullString = str(node)
    if 'hydrant' in fullString:
        propType = ToontownGlobals.AnimPropTypes.Hydrant
    elif 'trashcan' in fullString:
        propType = ToontownGlobals.AnimPropTypes.Trashcan
    elif 'mailbox' in fullString:
        propType = ToontownGlobals.AnimPropTypes.Mailbox
    return propType
