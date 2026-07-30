from toontown.toonbase.ToontownGlobals import *
from toontown.coghq import MintProduct

class MintShelf(MintProduct.MintProduct):
    Models = {CashbotMintIntA: 'phase_10/models/cashbotHQ/shelf_A1MoneyBags',
     CashbotMintIntB: 'phase_10/models/cashbotHQ/shelf_A1Money',
     CashbotMintIntC: 'phase_10/models/cashbotHQ/shelf_A1Gold'}
    Scales = {CashbotMintIntA: 1.0,
     CashbotMintIntB: 1.0,
     CashbotMintIntC: 1.0}
