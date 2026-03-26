local M = {}

M.object = {
    id = "REQUIREMENT",
    long_name = "REQUIREMENT",
    description = "Imported from ReqIF",
    pid_prefix = "REQUIREMEN",
    attributes = {
        { name = "MID", type = "STRING" },
        { name = "NOTES", type = "STRING" },
        { name = "RATIONALE", type = "STRING" },
        { name = "STATUS", type = "STRING" },
    }
}

return M
