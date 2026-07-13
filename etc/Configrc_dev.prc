# Local dev overrides (safe to edit/delete).

# Enable shard flow breadcrumbs + hang watchdog stack dumps.
shard-debug 1

# Make local testing easier (Astron dev login is keyed off username in astron/databases/accounts.json).
required-login auto

# Launcher/UI revamp
want-modern-launcher-ui 1
# Automatically start Astron/UberDOG/AI on client launch (Windows dev flow).
auto-start-local-servers 1
# If 1, server scripts open visible consoles (useful for debugging).
local-servers-show-consoles 0
# If 1, pipe server stdout/stderr into the client console.
local-servers-forward-logs 1
# Even if MD is already running, spawn UberDOG/AI so their logs can be forwarded.
local-servers-always-spawn-python 1
# If login succeeds then drops (10053) or loops error 100, CA may be up while UberDOG died — after killing
# orphaned ppython UD/AI, uncomment ONE of:
# local-servers-force-python-spawn 1
# local-servers-skip-python-if-ca-open 0

# Pick-a-Toon: render UI over a TTC backdrop when available.
want-pick-a-toon-ttc-backdrop 1
# Optional: enable OutdoorLighting on the TTC backdrop (can be expensive / risky).
pick-a-toon-ttc-backdrop-want-lighting 0

# If something still insists on a playToken path, provide one.
fake-playtoken dev

# Extra visibility.
default-directnotify-level info
notify-level-OTPClientRepository info

# Off during normal play: when enabled, every C++ event updates a Python dict (expensive
# during loader/interest bursts and makes hitches worse).
eventmanager-debug-flood #f
# Cheap flood diagnosis: for small persistent floods (processed ~10-100),
# use stride=1 so the "top names" list actually populates.
eventmanager-flood-approx-stride 1
# Never drain the queue on flood: clearing it drops async/interest completion events
# and the client fails to finish shard entry or hood load (silent exit / hang).
eventmanager-drain-on-flood #f
# See Configrc.prc: huge values = one doEvents() blocks for seconds; 50k/frame is a balance.
eventmanager-max-events-per-frame 50000