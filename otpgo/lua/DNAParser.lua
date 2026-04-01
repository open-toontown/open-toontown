local filepath = require("filepath")

function searchForDNAFiles()
    local dnaFiles = {}

    -- TODO: Custom search path
    local foundFiles = filepath.glob('../resources/phase_*/dna/*.dna')
    for _, file in ipairs(foundFiles) do
        -- Skip storage files as they have no visgroups.
        if not string.find(file, "storage") then
            table.insert(dnaFiles, file)
        end
    end
    return dnaFiles
end


function parseDNAFile(filename, vismap)
    local file = assert(io.open(filename, "r"), string.format("Failed to open DNA file \"%s\"", filename))

    -- Extract the zone id from the filename if there is any (_2100.dna, _2200.dna, etc.)
    local zoneId = filename:match("_(%d+)%.dna$")

    local currentGroup = nil
    local depth = 0

    for line in file:lines() do
        -- Trim whitespace
        line = line:match("^%s*(.-)%s*$")

        -- Detect visgroup start
        local groupId = line:match('visgroup%s+"(.-)"%s*%[')
        if groupId then
            -- Split the ":" character if there is any
            groupId = string.split(groupId, ":")[1]
            currentGroup = groupId
            vismap[currentGroup] = {}
            depth = 1
        elseif currentGroup then
            -- Track nested brackets
            if line:find("%[") then depth = depth + 1 end
            if line:find("%]") then depth = depth - 1 end

            -- Extract visible entries
            local visibles = line:match('vis%s*%[(.-)%]')
            if visibles then
                for id in visibles:gmatch('"(.-)"') do
                    -- Split the ":" character if there is any
                    id = string.split(id, ":")[1]
                    table.insert(vismap[currentGroup], tonumber(id))
                end
            end

            -- End of visgroup
            if depth == 0 then
                if not table.find(vismap[currentGroup], tonumber(currentGroup)) then
                    table.insert(vismap[currentGroup], tonumber(currentGroup))
                end
                if zoneId and not table.find(vismap[currentGroup], tonumber(zoneId)) then
                    table.insert(vismap[currentGroup], 1, tonumber(zoneId))
                end
                currentGroup = nil
            end
        end
    end
    file:close()
end
