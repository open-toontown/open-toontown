from . import CatalogFurnitureItem
from . import CatalogChatItem
from . import CatalogClothingItem
from . import CatalogEmoteItem
from . import CatalogWallpaperItem
from . import CatalogFlooringItem
from . import CatalogWainscotingItem
from . import CatalogMouldingItem
from . import CatalogWindowItem
from . import CatalogPoleItem
from . import CatalogPetTrickItem
from . import CatalogBeanItem
from . import CatalogGardenItem
from . import CatalogInvalidItem
from . import CatalogRentalItem
from . import CatalogGardenStarterItem
from . import CatalogNametagItem
from . import CatalogToonStatueItem
from . import CatalogAnimatedFurnitureItem
from . import CatalogAccessoryItem
INVALID_ITEM = 0
FURNITURE_ITEM = 1
CHAT_ITEM = 2
CLOTHING_ITEM = 3
EMOTE_ITEM = 4
WALLPAPER_ITEM = 5
WINDOW_ITEM = 6
FLOORING_ITEM = 7
MOULDING_ITEM = 8
WAINSCOTING_ITEM = 9
POLE_ITEM = 10
PET_TRICK_ITEM = 11
BEAN_ITEM = 12
GARDEN_ITEM = 13
RENTAL_ITEM = 14
GARDENSTARTER_ITEM = 15
NAMETAG_ITEM = 16
TOON_STATUE_ITEM = 17
ANIMATED_FURNITURE_ITEM = 18
ACCESSORY_ITEM = 19
NonPermanentItemTypes = (RENTAL_ITEM,)
CatalogItemTypes = {CatalogInvalidItem.CatalogInvalidItem: INVALID_ITEM,
 CatalogFurnitureItem.CatalogFurnitureItem: FURNITURE_ITEM,
 CatalogChatItem.CatalogChatItem: CHAT_ITEM,
 CatalogClothingItem.CatalogClothingItem: CLOTHING_ITEM,
 CatalogEmoteItem.CatalogEmoteItem: EMOTE_ITEM,
 CatalogWallpaperItem.CatalogWallpaperItem: WALLPAPER_ITEM,
 CatalogWindowItem.CatalogWindowItem: WINDOW_ITEM,
 CatalogFlooringItem.CatalogFlooringItem: FLOORING_ITEM,
 CatalogMouldingItem.CatalogMouldingItem: MOULDING_ITEM,
 CatalogWainscotingItem.CatalogWainscotingItem: WAINSCOTING_ITEM,
 CatalogPoleItem.CatalogPoleItem: POLE_ITEM,
 CatalogPetTrickItem.CatalogPetTrickItem: PET_TRICK_ITEM,
 CatalogBeanItem.CatalogBeanItem: BEAN_ITEM,
 CatalogGardenItem.CatalogGardenItem: GARDEN_ITEM,
 CatalogRentalItem.CatalogRentalItem: RENTAL_ITEM,
 CatalogGardenStarterItem.CatalogGardenStarterItem: GARDENSTARTER_ITEM,
 CatalogNametagItem.CatalogNametagItem: NAMETAG_ITEM,
 CatalogToonStatueItem.CatalogToonStatueItem: TOON_STATUE_ITEM,
 CatalogAnimatedFurnitureItem.CatalogAnimatedFurnitureItem: ANIMATED_FURNITURE_ITEM,
 CatalogAccessoryItem.CatalogAccessoryItem: ACCESSORY_ITEM}
CatalogItemType2multipleAllowed = {INVALID_ITEM: False,
 FURNITURE_ITEM: True,
 CHAT_ITEM: False,
 CLOTHING_ITEM: False,
 EMOTE_ITEM: False,
 WALLPAPER_ITEM: True,
 WINDOW_ITEM: True,
 FLOORING_ITEM: True,
 MOULDING_ITEM: True,
 WAINSCOTING_ITEM: True,
 POLE_ITEM: False,
 PET_TRICK_ITEM: False,
 BEAN_ITEM: False,
 GARDEN_ITEM: False,
 RENTAL_ITEM: False,
 GARDENSTARTER_ITEM: False,
 NAMETAG_ITEM: False,
 TOON_STATUE_ITEM: False,
 ANIMATED_FURNITURE_ITEM: True,
 ACCESSORY_ITEM: False}
SingleCodeRedemption = (BEAN_ITEM,)
CatalogItemTypeMask = 31
CatalogItemSaleFlag = 128
CatalogItemGiftTag = 64
