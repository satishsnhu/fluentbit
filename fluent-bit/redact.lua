function redact_pii(tag, timestamp, record)
    local log = record["log"]
    if log then
        -- emails
        log = string.gsub(log, "[%w._%%+-]+@[%w.-]+%.[%a]+", "****@****")
        -- ssn
        log = string.gsub(log, "%d%d%d[- .]?%d%d[- .]?%d%d%d%d", "***-**-****")
        -- phone
        log = string.gsub(log, "%d%d%d[- .]?%d%d%d[- .]?%d%d%d%d", "***-***-****")
        record["log"] = log
    end
    return 1, timestamp, record
end
