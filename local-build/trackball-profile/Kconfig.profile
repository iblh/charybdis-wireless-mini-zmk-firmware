config PMW3610_ALT_PROFILE
    bool "Low-rate optical and motion pipeline diagnostics"
    depends on PMW3610_ALT && LOG && BT
    default n
