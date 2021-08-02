# Window Settings
window-title Toontown
icon-filename phase_3/models/gui/toontown.ico
cursor-filename phase_3/models/gui/toonmono.cur

# Audio/Video
audio-library-name p3openal_audio
load-display pandagl
aux-display pandagl
aux-display pandadx9
aux-display tinydisplay
depth-bits 24
audio-sfx-active #t
audio-music-active #t
aspect-ratio 1.333333

# Models/Resources
model-path resources
default-model-extension .bam
vfs-case-sensitive 0

# Server Settings
server-version sv1.0.47.38
server-failover 80 443
tt-specific-login 1
# If true, individual TCP packets are not sent immediately, but rather they are collected together and accumulated to be sent periodically as one larger TCP packet.  This cuts down on overhead from the TCP/IP protocol, especially if many small packets need to be sent on the same connection, but it introduces additional latency (since packets must be held before they can be sent).
collect-tcp 1

# Developer Options
want-dev 0
schellgames-dev 0

# DC Files
dc-file etc/toon.dc
dc-file etc/otp.dc

# HTTP/Downloading
verify-ssl 0
downloader-timeout-retries 4
downloader-byte-rate 125000
downloader-frequency 0.1
http-connect-timeout 20
http-timeout 30
extra-ssl-handshake-time 20.0
# Compute the SSL random seed early on.
early-random-seed 1

# Notify Settings
notify-level-collide warning
notify-level-chan warning
notify-level-gobj warning
notify-level-loader warning
notify-timestamp #t
notify-integrate #f
default-directnotify-level info
console-output 1

# Panda3D/DirectX
# Configure this true if you have a buggy graphics driver that doesn't correctly implement the third parameter, NumVertices, of DrawIndexedPrimitive().  In particular, the NVIDIA Quadro driver version 6.14.10.7184 seems to treat this as a maximum vertex index, rather than a delta between the maximum and minimum vertex index.  Turn this on if you are seeing stray triangles, or you are not seeing all of your triangles.  Enabling this should work around this bug, at the cost of some additional rendering overhead on the GPU. 
dx-broken-max-index 1
# Set this true to show ime texts on the chat panel and hide the IME default windows. This is a mechanism to work around DX8/9 interface.
ime-aware 1
# Set this true to hide ime windows.
ime-hide 1
# Use DirectX management of video memory
dx-management 1
# If this is true, more accurate but more expensive fog computations are performed.
dx-use-rangebased-fog #t
# Set this true to have all CollisionTraversers in the world respect the previous frame's transform (position) for a given object when determining motion for collision tests.
respect-prev-transform 1
# Specifies the maximum amount of time that should be consumed by a single call to Decompressor::run().
decompressor-step-time 0.5
# Specifies the maximum amount of time that should be consumed by a single call to Extractor::step().
extractor-step-time 0.5
# Fix for Panda3D 1.0.0
temp-hpr-fix 1
# Set this true to allow the use of vertex buffers (or buffer objects, as OpenGL dubs them) for rendering vertex data.
vertex-buffers 0

# GUI Settings
direct-wtext 0
on-screen-debug-font ImpressBT.ttf

# Misc Settings
inactivity-timeout 180
# If require-window is true, it means that we should raise an exception if the window fails to open correctly.
require-window 0
# Limits the size of the buffer used.
patcher-buffer-size 512000
# required-login: auto, green, blue, playToken, DISLToken, gameServer.
required-login playToken
# Do we merge or isolate LOD's?
merge-lod-bundles 0
early-event-sphere 1
# This controls the default value of SmoothMover::get_accept_clock_skew().
accept-clock-skew 1
text-minfilter linear_mipmap_linear
gc-save-all 0
server-data-folder data
