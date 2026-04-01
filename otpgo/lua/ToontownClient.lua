package.path = package.path .. ";lua/?.lua"

local inspect = require('inspect')
local date = require('date')

-- Load Utils:
dofile("lua/Utils.lua")

-- Load DNAParser:
dofile("lua/DNAParser.lua")

-- Generate vismap from DNA files:
local dnaFiles = searchForDNAFiles()

VISMAP = {}
for _, filePath in ipairs(dnaFiles) do
    print(string.format('ToontownClient: Reading DNA File \"%s\"', filePath))
    parseDNAFile(filePath, VISMAP)
end
print("ToontownClient: Vismap successfully loaded.")

-- Read account bridge:
function readAccountBridge()
    local json = require("json")
    local io = require("io")

    -- TODO: Custom path.
    f, err = io.open("databases/accounts.json", "r")
    if err then
        print("ToontownClient: Returning empty table for account bridge")
        return {}
    end

    decoder = json.new_decoder(f)
    result, err = decoder:decode()
    f:close()
    assert(not err, err)
    print("ToontownClient: Account bridge successfully loaded.")
    return result
end

ACCOUNT_BRIDGE = readAccountBridge()

function saveAccountBridge()
    local json = require("json")
    local io = require("io")

    -- TODO: Custom path.
    f, err = io.open("databases/accounts.json", "w")
    assert(not err, err)
    encoder = json.new_encoder(f)
    err = encoder:encode(ACCOUNT_BRIDGE)
    assert(not err, err)
end

NAME_PATTERNS = {}

-- Read name patterns:
function readNamePatterns()
    local io = require("io")

    local f, err = io.open("../resources/phase_3/etc/NameMasterEnglish.txt")
    assert(not err, err)

    for line in f:lines() do
        if string.starts(line, "#") then
            goto continue
        end

        local parsed = {}

        -- Match any character except "*"
        for w in string.gmatch(line, "([^*]+)") do
            table.insert(parsed, w)
        end

        if #parsed ~= 3 then
            print(string.format("readNamePatterns: Invalid entry: %s", inspect(parsed)))
            goto continue
        end

        table.insert(NAME_PATTERNS, parsed[3])
        ::continue::
    end

    print("ToontownClient: Name patterns successfully loaded.")
end

readNamePatterns()

-- Load message types:
dofile("lua/MsgTypes.lua")

-- Load Toon DNA helpers:
dofile("lua/ToonDNA.lua")

function receiveDatagram(client, dgi)
    -- Client received datagrams
    msgType = dgi:readUint16()

    if msgType == CLIENT_HEARTBEAT then
        client:handleHeartbeat()
    elseif msgType == CLIENT_DISCONNECT then
        client:handleDisconnect()
    elseif msgType == CLIENT_LOGIN_TOONTOWN then
        handleLoginToontown(client, dgi)
    -- We have reached the only message types unauthenticated clients can use.
    elseif not client:authenticated() then
        client:sendDisconnect(CLIENT_DISCONNECT_GENERIC, "First datagram is not CLIENT_LOGIN_TOONTOWN", true)
    elseif msgType == CLIENT_ADD_INTEREST then
        handleAddInterest(client, dgi)
    elseif msgType == CLIENT_REMOVE_INTEREST then
        client:handleRemoveInterest(dgi)
    elseif msgType == CLIENT_GET_AVATARS then
        handleGetAvatars(client, false)
    elseif msgType == CLIENT_OBJECT_UPDATE_FIELD then
        client:handleUpdateField(dgi)
    elseif msgType == CLIENT_CREATE_AVATAR then
        handleCreateAvatar(client, dgi)
    elseif msgType == CLIENT_SET_NAME_PATTERN then
        handleSetNamePattern(client, dgi)
    elseif msgType == CLIENT_SET_AVATAR then
        handleSetAvatar(client, dgi)
    elseif msgType == CLIENT_GET_FRIEND_LIST then
        handleGetFriendList(client)
    elseif msgType == CLIENT_OBJECT_LOCATION then
        client:setLocation(dgi)
    else
        client:sendDisconnect(CLIENT_DISCONNECT_GENERIC, string.format("Unknown message type: %d", msgType), true)
    end

    if dgi:getRemainingSize() ~= 0 then
        client:sendDisconnect(CLIENT_DISCONNECT_OVERSIZED_DATAGRAM, string.format("Datagram contains excess data.\n%s", tostring(dgi)), true)
    end
end

function handleLoginToontown(client, dgi)
    local playToken = dgi:readString()
    local version = dgi:readString()
    local hash = dgi:readUint32()
    local tokenType = dgi:readInt32()
    local wantMagicWords = dgi:readString()

    if client:authenticated() then
        client:sendDisconnect(CLIENT_DISCONNECT_RELOGIN, "Authenticated client tried to login twice!", true)
        return
    end

    -- Check if version and hash matches
    if version ~= SERVER_VERSION then
        client:sendDisconnect(CLIENT_DISCONNECT_BAD_VERSION, string.format("Client version mismatch: client=%s, server=%s", version, SERVER_VERSION), true)
        return
    end

    if hash ~= DC_HASH then
        client:sendDisconnect(CLIENT_DISCONNECT_BAD_VERSION, string.format("Client DC hash mismatch: client=%d, server=%d", hash, DC_HASH), true)
        return
    end

    -- TODO: Make these configurable.
    local speedChatPlus = true
    local openChat = true
    local isPaid = true
    local dislId = 1
    local linkedToParent = false

    local accountId = ACCOUNT_BRIDGE[playToken]
    if accountId ~= nil then
        -- Query the account object
        client:getDatabaseValues(accountId, "Account", {"ACCOUNT_AV_SET", "CREATED", "LAST_LOGIN"}, function (doId, success, fields)
            if not success then
                client:sendDisconnect(CLIENT_DISCONNECT_ACCOUNT_ERROR, "The Account object was unable to be queried.", true)
                return
            end

            -- Update LAST_LOGIN
            fields.LAST_LOGIN = os.date("%a %b %d %H:%M:%S %Y")
            client:setDatabaseValues(accountId, "Account", {
                LAST_LOGIN = fields.LAST_LOGIN,
            })

            loginAccount(client, fields, accountId, playToken, openChat, isPaid, dislId, linkedToParent, speedChatPlus)
        end)
    else
        -- Create a new account object
        local account = {
            -- The rest of the values are defined in the dc file.
            CREATED = os.date("%a %b %d %H:%M:%S %Y"),
            LAST_LOGIN = os.date("%a %b %d %H:%M:%S %Y"),
        }

        client:createDatabaseObject("Account", account, DATABASE_OBJECT_TYPE_ACCOUNT, function (accountId)
            if accountId == 0 then
                client:sendDisconnect(CLIENT_DISCONNECT_ACCOUNT_ERROR, "The Account object was unable to be created.", false)
                return
            end

            -- Store the account into the bridge
            ACCOUNT_BRIDGE[playToken] = accountId
            saveAccountBridge()

            account.ACCOUNT_AV_SET = {0, 0, 0, 0, 0, 0}

            client:writeServerEvent("account-created", "ToontownClient", string.format("%d", accountId))

            loginAccount(client, account, accountId, playToken, openChat, isPaid, dislId, linkedToParent, speedChatPlus)
        end)
    end
end

function loginAccount(client, account, accountId, playToken, openChat, isPaid, dislId, linkedToParent, speedChatPlus)
    -- Eject other client if already logged in.
    local ejectDg = datagram:new()
    client:addServerHeaderWithAccountId(ejectDg, accountId, CLIENTAGENT_EJECT)
    ejectDg:addUint16(100)
    ejectDg:addString("You have been disconnected because someone else just logged in using your account on another computer.")
    client:routeDatagram(ejectDg)

    -- Subscribe to our puppet channel.
    client:subscribePuppetChannel(accountId, 3)

    -- Set our channel containing our account id
    client:setChannel(accountId, 0)

    client:authenticated(true)

    -- Store the account id and avatar list into our client's user table:
    local userTable = client:userTable()
    userTable.accountId = accountId
    userTable.avatars = account.ACCOUNT_AV_SET
    userTable.playToken = playToken
    userTable.isPaid = isPaid
    userTable.speedChatPlus = speedChatPlus
    userTable.openChat = openChat
    client:userTable(userTable)

    -- Log the event
    client:writeServerEvent("account-login", "ToontownClient", string.format("%d", accountId))

    -- Prepare the login response.
    local resp = datagram:new()
    resp:addUint16(CLIENT_LOGIN_TOONTOWN_RESP)
    resp:addUint8(0) -- Return code
    resp:addString("All Ok")
    resp:addUint32(dislId) -- accountNumber
    resp:addString(playToken) -- accountName
    resp:addUint8(1) -- accountNameApproved

    if openChat then
        resp:addString('YES') -- openChatEnabled, does not seem to be used
    else
        resp:addString('NO') -- openChatEnabled, does not seem to be used
    end

    resp:addString('YES') -- createFriendsWithChat
    resp:addString('YES') -- chatCodeCreationRule
    resp:addUint32(os.time()) -- sec
    resp:addUint32(os.clock()) -- usec

    if isPaid then
        resp:addString("FULL") -- access
    else
        resp:addString("VELVET") -- access
    end

    if speedChatPlus then
        resp:addString("YES") -- WhiteListResponse
    else
        resp:addString("NO") -- WhiteListResponse
    end

    resp:addString(os.date("%Y-%m-%d %H:%M:%S")) -- lastLoggedInStr
    resp:addInt32(math.floor(date.diff(account.LAST_LOGIN, account.CREATED):spandays())) -- accountDays

    if linkedToParent then
        resp:addString("WITH_PARENT_ACCOUNT") -- toonAccountType
    else
        resp:addString("NO_PARENT_ACCOUNT") -- toonAccountType
    end

    resp:addString(playToken) -- userName

    -- Dispatch the response to the client.
    client:sendDatagram(resp)
end

function handleAddInterest(client, dgi)
    local handle = dgi:readUint16()
    local context = dgi:readUint32()
    local parent = dgi:readUint32()
    local zones = {}
    while dgi:getRemainingSize() > 0 do
        local zone = dgi:readUint32()
        if zone == 1 then
            -- We don't want quiet zone.
            goto continue
        end

        table.insert(zones, zone)
        ::continue::
    end

    -- Replace street zone with vismap if exists
    if #zones == 1 then
        if VISMAP[tostring(zones[1])] ~= nil then
            zones = VISMAP[tostring(zones[1])]
        elseif zones[1] >= 22000 and zones[1] < 61000 then
            -- Handle Welcome Valley zones
            local welcomeValleyZone = zones[1]
            local hoodId = zones[1] - math.fmod(zones[1], 1000)
            local offset = math.fmod(welcomeValleyZone, 2000)
            -- Get original vismap
            if VISMAP[tostring(offset + 2000)] ~= nil then
                zones = table.shallow_copy(VISMAP[tostring(offset + 2000)])
                for i, v in ipairs(zones) do
                    local offset = math.fmod(zones[i], 2000)
                    zones[i] = offset + hoodId
                end
            end
        end
    end

    client:handleAddInterest(handle, context, parent, zones)
end

function handleGetAvatars(client, deletion)
    local userTable = client:userTable()
    local avatarList = userTable.avatars

    local retreivedFields = {}
    local expectingAvatars = {}
    local gotAvatars = {}

    local function gotAllAvatars()
        dg = datagram:new()
        local msgType = CLIENT_GET_AVATARS_RESP
        if deletion then
            msgType = CLIENT_DELETE_AVATAR_RESP
        end

        dg:addUint16(msgType)
        dg:addUint8(0) -- returnCode
        dg:addUint16(#gotAvatars) -- avatarTotal
        for index, fields in pairs(retreivedFields) do
            local wishNameState = fields.WishNameState[1]
            local wishName = fields.WishName[1]

            local aName = 0

            local wantName = ""
            local approvedName = ""
            local rejectedName = ""

            if wishNameState == "OPEN" then
                aName = 1
            end

            if wishNameState == "PENDING" then
                wantName = wishName
            end

            if wishNameState == "APPROVED" then
                approvedName = wishName
            end

            if wishNameState == "REJECTED" then
                rejectedName = wishName
            end

            dg:addUint32(fields.avatarId)
            dg:addString(fields.setName[1]) -- name
            dg:addString(wantName) -- wantName
            dg:addString(approvedName) -- approvedName
            dg:addString(rejectedName) -- rejectedName

            dg:addString(fields.setDNAString[1]) -- avDNA
            dg:addUint8(index - 1) -- avPosition
            dg:addUint8(aName) -- aName
        end

        client:sendDatagram(dg)
    end

    for index, avatarId in ipairs(avatarList) do
        if avatarId ~= 0 then
            -- Query the avatar object
            client:getDatabaseValues(avatarId, "DistributedToon", {"setName", "setDNAString", "WishNameState", "WishName"}, function (doId, success, fields)
                if not success then
                    client:sendDisconnect(CLIENT_DISCONNECT_ACCOUNT_ERROR, string.format("The DistributedToon object %d was unable to be queried.", avatarId), false)
                    return
                end

                fields.avatarId = avatarId
                retreivedFields[index] = fields
                table.insert(gotAvatars, {})
                if #gotAvatars == #expectingAvatars then
                    gotAllAvatars()
                end
            end)

            table.insert(expectingAvatars, avatarId)
        end

        if index == 6 and #expectingAvatars == 0 then
            -- We got nothing to do.
            gotAllAvatars()
        end
    end
end

function handleCreateAvatar(client, reader)
    local userTable = client:userTable()
    local accountId = userTable.accountId

    local contextId = reader:readUint16()
    local dnaString = reader:readString()
    local avPosition = reader:readUint8()

    if avPosition > 6 then
        -- Client sent an invalid av position
        client:sendDisconnect(CLIENT_DISCONNECT_GENERIC, "Invalid Avatar index chosen.", true)
        return
    end

    if userTable.avatars[avPosition + 1] ~= 0 then
        -- This index isn't available.
        client:sendDisconnect(CLIENT_DISCONNECT_ACCOUNT_ERROR, "The Avatar index chosen is not available.", true)
        return
    end

    local result, dna = isValidNetString(dnaString)

    if not result then
        client:sendDisconnect(CLIENT_DISCONNECT_ACCOUNT_ERROR, "Invalid Avatar DNA sent.", true)
        return
    end

    -- Create a new DistributedToon object
    local avatar = {
        -- The rest of the values are defined in the dc file.
        setName = {NumToColor[dna[1]] .. " " .. AnimalToSpecies[dna[2]]},
        setDISLid = {accountId},
        setDNAString = {dnaString},
        setPosIndex = {avPosition},
        setAccountName = {userTable.playToken},
        WishNameState = {"OPEN"},
    }

    client:createDatabaseObject("DistributedToon", avatar, DATABASE_OBJECT_TYPE_TOON, function (avatarId)
        if avatarId == 0 then
            client:sendDisconnect(CLIENT_DISCONNECT_ACCOUNT_ERROR, "The DistributedToon object was unable to be created.", false)
            return
        end

        userTable.avatars[avPosition + 1] = avatarId

        client:setDatabaseValues(accountId, "Account", {
            ACCOUNT_AV_SET = userTable.avatars,
        })

        client:writeServerEvent("avatar-created", "ToontownClient", string.format("%d|%d", accountId, avatarId))

        -- Prepare the create avatar response.
        local resp = datagram:new()
        resp:addUint16(CLIENT_CREATE_AVATAR_RESP)
        resp:addUint16(contextId)
        resp:addUint8(0) -- returnCode
        resp:addUint32(avatarId)

        -- Dispatch the response to the client.
        client:sendDatagram(resp)
    end)
end

function handleSetNamePattern(client, dgi)
    local avId = dgi:readUint32()

    client:getDatabaseValues(avId, "DistributedToon", {"WishNameState"}, function (doId, success, fields)
        if not success then
            client:sendDisconnect(CLIENT_DISCONNECT_ACCOUNT_ERROR, string.format("The DistributedToon object %d was unable to be queried.", avId), false)
            return
        end

        if fields.WishNameState[1] ~= "OPEN" then
            -- Only one name allowed!
            client:sendDisconnect(CLIENT_DISCONNECT_ACCOUNT_ERROR, string.format("The DistributedToon object %d is unable to be named.", avId), true)
            return
        end
    end)

    local p1 = dgi:readInt16()
    local f1 = dgi:readInt16()
    local p2 = dgi:readInt16()
    local f2 = dgi:readInt16()
    local p3 = dgi:readInt16()
    local f3 = dgi:readInt16()
    local p4 = dgi:readInt16()
    local f4 = dgi:readInt16()

    -- Construct a pattern.
    local pattern = {{p1, f1}, {p2, f2},
                     {p3, f3}, {p4, f4}}

    local parts = {}
    for _, pair in ipairs(pattern) do
        local p, f = pair[1], pair[2]
        local part = NAME_PATTERNS[p + 1]
        if part == nil then
            part = ""
        end

        if f then
            string.upperFirst(part)
        else
            string.lower(part)
        end

        table.insert(parts, part)
    end

    -- Merge 3&4 (the last name) as there should be no space.
    parts[3] = parts[3] .. table.remove(parts, 4)

    for i = #parts, 1, -1 do
        if parts[i] == "" then
            table.remove(parts, i)
        end
    end

    local name = table.concat(parts, " ")

    client:setDatabaseValues(avId, "DistributedToon", {
        WishNameState = {"LOCKED"},
        WishName = {""},
        setName = {name}
    })

    resp = datagram:new()
    resp:addUint16(CLIENT_SET_NAME_PATTERN_ANSWER)
    resp:addUint32(avId)
    resp:addUint8(0)

    client:sendDatagram(resp)
end

function checkIsAvInList(avatarId, avatarList)
    local isAvInList = false
    for _, avId in ipairs(avatarList) do
        if avatarId == avId then
            isAvInList = true
            break
        end
    end

    return isAvInList
end

function handleSetAvatar(client, dgi)
    local userTable = client:userTable()
    local accountId = userTable.accountId

    local avatarId = dgi:readUint32()

    if avatarId == 0 then
        clearAvatar(client)
        return
    end

    local isAvInList = checkIsAvInList(avatarId, userTable.avatars)
    if not isAvInList then
        client:sendDisconnect(CLIENT_DISCONNECT_GENERIC, string.format("Avatar %d not in list.", avatarId), true)
        return
    end

    userTable.avatarId = avatarId
    userTable.friendQueue = {}
    client:userTable(userTable)

    client:setChannel(accountId, avatarId)

    local setAccess = 1
    if userTable.isPaid then
        setAccess = 2
    end

    client:sendActivateObject(avatarId, "DistributedToon", {
        setAccess = {setAccess},
    })

    client:objectSetOwner(avatarId, true)

    -- Let the UberDOG know about our avatar usage.
    sendUsage(client, userTable.playToken, userTable.openChat, 0, avatarId, accountId, userTable.isPaid, false)

    -- Let the UberDOG know about our avatar usage (going offline).
    sendUsage(client, userTable.playToken, userTable.openChat, avatarId, 0, accountId, userTable.isPaid, true)
end

function sendUsage(client, playToken, openChat, priorAvatar, newAvatar, accountId, isPaid, postRemove)
    -- Log avatar usage
    local playerName = playToken
    local playerNameApproved = 1
    local openChatEnabled = "NO"

    if openChat then
        openChatEnabled = "YES"
    end

    local createFriendsWithChat = "YES"
    local chatCodeCreation = "YES"

    local avatarId

    if priorAvatar ~= 0 then
        avatarId = priorAvatar
    else
        avatarId = newAvatar
    end

    local dg = datagram:new()
    dg:addServerHeader(CHANNEL_PUPPET_ACTION, avatarId, ACCOUNT_AVATAR_USAGE)

    dg:addUint32(priorAvatar) -- priorAvatar
    dg:addUint32(newAvatar) -- newAvatar
    dg:addUint16(0) -- newAvatarType
    dg:addUint32(accountId) -- accountId
    dg:addString(openChatEnabled) -- openChatEnabled
    dg:addString(createFriendsWithChat) -- createFriendsWithChat
    dg:addString(chatCodeCreation) -- chatCodeCreation

    if isPaid then
        dg:addString("FULL") -- piratesAccess
    else
        dg:addString("VELVET") -- piratesAccess
    end

    dg:addInt32(0) -- familyAccountId
    dg:addInt32(accountId) -- playerAccountId

    dg:addString(playerName) -- playerName
    dg:addInt8(playerNameApproved) -- playerNameApproved

    -- maxAvatars
    local maxAvatars

    if isPaid then
        maxAvatars = 6
    else
        maxAvatars = 1
    end

    dg:addInt32(maxAvatars) -- maxAvatars

    dg:addInt16(0) -- numFamilyMembers

    if postRemove then
        client:addPostRemove(dg)
    else
        client:routeDatagram(dg)
    end
end

function clearAvatar(client)
    local userTable = client:userTable()

    if userTable.avatarId == nil then
        return
    end

    client:removeSessionObject(userTable.avatarId)
    client:unsubscribePuppetChannel(userTable.avatarId, 1)

    dg = datagram:new()
    client:addServerHeader(dg, userTable.avatarId, STATESERVER_OBJECT_DELETE_RAM)
    dg:addUint32(userTable.avatarId)
    client:routeDatagram(dg)

    client:clearPostRemoves()

    userTable.avatarId = nil
    userTable.friendsList = nil
    client:userTable(userTable)

    client:setChannel(userTable.accountId, 0)
end

function handleAddOwnership(client, doId, parent, zone, dc, dgi)
    local userTable = client:userTable()
    local accountId = userTable.accountId
    local avatarId = userTable.avatarId

    if doId ~= avatarId then
        client:warn(string.format("Got AddOwnership for object %d, our avatarId is %d", doId, avatarId))
        return
    end

    client:addSessionObject(doId)
    client:subscribePuppetChannel(avatarId, 1)

    -- Store name for SpeedChat Plus
    local name = dgi:readString()
    userTable.avatarName = name
    client:userTable(userTable)

    local remainder = dgi:readRemainder()

    client:writeServerEvent("selected-avatar", "ToontownClient", string.format("%d|%d", accountId, avatarId))

    local resp = datagram:new()
    resp:addUint16(CLIENT_GET_AVATAR_DETAILS_RESP)
    resp:addUint32(doId) -- avatarId
    resp:addUint8(0) -- returnCode
    resp:addString(name) -- setName
    resp:addData(remainder)
    client:sendDatagram(resp)

    -- Update common chat flags:
    local dg = datagram:new()
    dg:addServerHeader(avatarId, avatarId, STATESERVER_OBJECT_UPDATE_FIELD)
    dg:addUint32(avatarId)
    client:packFieldToDatagram(dg, "DistributedToon", "setCommonChatFlags", {0}, true)
    client:routeDatagram(dg)

    -- Update whitelist chat flags:
    local dg = datagram:new()
    dg:addServerHeader(avatarId, avatarId, STATESERVER_OBJECT_UPDATE_FIELD)
    dg:addUint32(avatarId)
    if userTable.speedChatPlus then
        client:packFieldToDatagram(dg, "DistributedToon", "setWhitelistChatFlags", {1}, true)
    else
        client:packFieldToDatagram(dg, "DistributedToon", "setWhitelistChatFlags", {0}, true)
    end

    client:routeDatagram(dg)
end

function handleGetFriendList(client)
    -- TODO: Friends
    local resp = datagram:new()
    resp:addUint16(CLIENT_GET_FRIEND_LIST_RESP)
    resp:addUint8(0) -- errorCode
    resp:addUint16(0) -- count
    client:sendDatagram(resp)
end
