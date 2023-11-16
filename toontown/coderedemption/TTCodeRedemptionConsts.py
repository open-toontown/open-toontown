from panda3d.core import ConfigVariableInt

DefaultDbName = 'tt_code_redemption'
RedeemErrors = Enum('Success, CodeDoesntExist, CodeIsInactive, CodeAlreadyRedeemed, AwardCouldntBeGiven, TooManyAttempts, SystemUnavailable, ')
RedeemErrorStrings = {RedeemErrors.Success: 'Success',
 RedeemErrors.CodeDoesntExist: 'Invalid code',
 RedeemErrors.CodeIsInactive: 'Code is inactive',
 RedeemErrors.CodeAlreadyRedeemed: 'Code has already been redeemed',
 RedeemErrors.AwardCouldntBeGiven: 'Award could not be given',
 RedeemErrors.TooManyAttempts: 'Too many attempts, code ignored',
 RedeemErrors.SystemUnavailable: 'Code redemption is currently unavailable'}
MaxCustomCodeLen = ConfigVariableInt('tt-max-custom-code-len', 16).getValue()
