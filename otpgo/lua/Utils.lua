-- From https://stackoverflow.com/a/22831842
function string.starts(str, start)
    return string.sub(str, 1, string.len(start)) == start
end

-- From https://stackoverflow.com/a/2421746
function string.upperFirst(str)
    return string.gsub(str, "^%l", string.upper)
end

function string.split(s, sep)
    local fields = {}
    -- Default separator is a space if not provided
    sep = sep or " "
    -- The pattern matches one or more characters that are NOT the separator
    local pattern = string.format("([^%s]+)", sep)

    -- Iterate over all matches and insert them into the table
    for match in string.gmatch(s, pattern) do
        table.insert(fields, match)
    end

    return fields
end

function table.shallow_copy(t)
    local t2 = {}
    for k, v in pairs(t) do
        t2[k] = v
    end
    return t2
end

function table.find(t, value)
    for i, v in ipairs(t) do
        if v == value then
            return i
        end
    end
    return nil
end
