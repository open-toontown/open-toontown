# GitHub Repository
https://github.com/ToontownSuperForeverMVP/TOONTOWN-BEST-THE-NEW-.git

# Project Overview
This repository contains **Toontown Super Forever MVP** (TOONTOWN-BEST-THE-NEW-), an open-source Toontown server and client codebase powered by Panda3D and Astron.

# Codebase Architecture & Structure
- **`toontown/`**: Main Toontown client logic, including game states, hoods, quest systems, shaders, GUI, and base files.
  - `toontown/hood/`: Outdoor lighting (`OutdoorLighting.py`) and procedural sky (`ProceduralSky.py`) features.
  - `toontown/launcher/`: Local server management, launcher routines, user options.
  - `toontown/quest/`: Quest system (`Quests.py`, `LegacyQuestDict.py`, `QuestParser.py`), `AutoerManager`, `TaskAutoer`.
  - `toontown/safezone/`: Crane sandboxes (`DistributedTTCCraneSandbox`, AI variant).
  - `toontown/shaders/`: Custom visual shaders (water, sky, sunrays).
  - `toontown/shtiker/`: Custom Shtiker Book pages (`AutoerPage`).
  - `toontown/toontowngui/`: Modern loading screens (`ModernLoadingScreen`, `LoadingAssetPreview`, `ZonePrefetchCatalog`, `ToontownLoadingScreen`).
- **`otp/`**: Online Toontown Protocol framework (common networking, avatar, chat, and distributed object classes).
- **`astron/`**: Server backend configuration, cluster definitions, and database schemas.
- **`autoers/`**: Bot scripts and quest automation modules.
- **`tools/`**: Development, maintenance, and asset management scripts.
- **`win32/`, `linux/`, `darwin/`**: Engine launcher scripts and platform-specific binaries/tools.

# Porting Plan: OutdoorLighting System & Procedural Taskline/Quests

Source: `C:\Users\Shadow\Desktop\scfo\supercfo`
Target: `C:\Users\Shadow\Desktop\ttbtn`

## Phase 1: Fully Updated OutdoorLighting System Port
- **Source Modules**:
  - `C:\Users\Shadow\Desktop\scfo\supercfo\OutdoorLighting.py` (212 KB full engine)
  - `C:\Users\Shadow\Desktop\scfo\supercfo\ProceduralSky.py` (19.7 KB procedural sky)
  - `C:\Users\Shadow\Desktop\scfo\supercfo\shaders\` (`sky.vert/frag.glsl`, `sunrays.vert/frag.glsl`, `water.vert/frag.glsl`)
- **Key Enhancements to Integrate into `toontown/hood/OutdoorLighting.py` & `toontown/hood/ProceduralSky.py`**:
  - Multithreaded Cull/Draw render-state safety (`_supportsBasicShaders()` GSG query & thread guards).
  - Dynamic shadow map depth-pass preservation (`ColorWriteAttrib` composition via `addAttrib()`).
  - `DepthOffsetAttrib` non-destructive application preventing Z-fighting on static geometry.
  - Soft light rig destruction preserving `_prevShadowCasterState` to eliminate day/night cycle rebuild blinks.
  - In-place video settings updates without freezing or window property deadlocks.
  - Sync GLSL shader assets to `toontown/shaders/`.

## Phase 2: Procedural Taskline & Quests System Port
- **Source Modules**:
  - `C:\Users\Shadow\Desktop\scfo\supercfo\toontown\quest\LegacyQuestDict.py` (15,743 lines of procedural quest chains)
  - `C:\Users\Shadow\Desktop\scfo\supercfo\toontown\quest\Quests.py` (Updated quest management & reward dict generators)
  - `C:\Users\Shadow\Desktop\scfo\supercfo\toontown\quest\QuestParser.py` (Dialogue script tokenizer/parser)
- **Key Enhancements to Integrate into `toontown/quest/`**:
  - Port `LegacyQuestDict.py` into `toontown/quest/LegacyQuestDict.py`.
  - Add `WANT_LEGACY_QUESTS` flag & dictionary merger in `toontown/quest/Quests.py`.
  - Update quest tier constants (`TT_TIER`, `DD_TIER`, `DG_TIER`, `MM_TIER`, `BR_TIER`, `DL_TIER`, `LAWBOT_HQ_TIER`, `BOSSBOT_HQ_TIER`, `ELDER_TIER`).
  - Add `questExists` compatibility helper for AI call sites.
  - Integrate `QuestParser.py` for tokenized dialogue scripts.
  - Ensure compatibility with `TaskAutoer.py` and `AutoerManager.py` quest automation engines.

## Phase 3: Integration & Verification
- Test client startup with `OutdoorLighting` and `ProceduralSky` enabled.
- Verify zone switching (TTC, DD, DG, MM, BR, DL, Cog HQs) under multi-threaded rendering mode.
- Verify quest assignment and completion in AI server repository (`QuestManagerAI.py`).

# Completed Work
- [x] Implemented `ModernLoadingScreen.py`: Full-screen launcher/game load screen with animated gradient background, pulsing lighting, progress bar, asset captions, tip dict support, and smooth outro fade sequence.
- [x] Implemented `LoadingAssetPreview.py`: Live 3D asset preview card rendering models, textures, fonts, and audio in an offscreen Panda3D buffer without interfering with main render world.
- [x] Implemented `ZonePrefetchCatalog.py`: Catalog mapping all hood zone IDs (TTC, DD, DG, MML, TB, DD, Speedway, Cog HQs, Estate) with async background preloading (`ZonePrefetchManager`).
- [x] Integrated `ToontownLoader.py` & `ToontownLoadingScreen.py`: Automatic asset callback forwarding, heartbeat keepalive, and fallback support.
- [x] Expanded `AssetCache.py`: Instant preloading of common Phase 3, 3.5, 4, 5 GUI models, chatboxes, shadows, and logos.
- [x] Ported updated `OutdoorLighting.py` (212 KB engine) and `ProceduralSky.py` into `toontown/hood/` with multi-threading guards and GSG depth-pass safety.
- [x] Ported GLSL shaders (`sky`, `sunrays`, `water`) into `toontown/shaders/` and added dynamic `_SHADER_DIR` resolution.
- [x] Ported `LegacyQuestDict.py` (15,29 procedural quest chains) and updated `toontown/quest/Quests.py` with `WANT_LEGACY_QUESTS` flag and `questExists()` helper.
- [x] Ported `QuestParser.py` into `toontown/quest/` and integrated `libotp` nametag/speech library dependencies.
- [x] Ported `toontown/settings/Settings.py`: Persistent JSON-backed settings manager with controls mapping, graphics/audio defaults, and property getters/setters.
- [x] Ported revamped `toontown/shtiker/OptionsPage.py` & `OptionsPageGUI.py`: Tabbed options page (Gameplay, Privacy, Controls, Video, Audio) with resolution pickers, anti-aliasing, FPS limiters, and lighting toggles.
- [x] Integrated `toontown/shtiker/ShtikerBook.py` & `toontown/toontowngui/ToontownScrolledFrame.py` with full OptionsPage support and localizations in `TTLocalizerEnglish.py`.
- [x] Ported Magic Word System (`toontown/spellbook/`): Integrated `MagicWordIndex.py` (340 magic words registered), `MagicWordConfig.py`, `TTOffMagicWordManager.py`, `TTOffMagicWordManagerAI.py`, and `ToontownMagicWordManager.py`.
- [x] Ported Spellbook Shtiker Page (`toontown/shtiker/WordPage.py`): Tabbed Spellbook page with search, category filters, copy-to-chat, argument inspectors, clothing ID tab, and accessory ID tabs.
- [x] Integrated `LocalToon.py` & `toontown/util/ui.py`: Registered `WordPage` in ShtikerBook and implemented `make_dsl_scrollable` wheel scrolling.
- [x] Submitted Pull Request #9 (`feature/modern-loading-system`), Pull Request #10 (`feature/outdoor-lighting-and-procedural-quests`), Pull Request #11 (`feature/settings-and-shtikerbook-revamp`), and Pull Request #12 (`feature/magic-words-and-spellbook-page`) to GitHub repository.

# TODO List for Future AI Instances
- [ ] Merge and review PR #9, PR #10, PR #11, and PR #12 into `develop`.
- [ ] Verify `TaskAutoer.py` quest automation compatibility with the procedural quest dict during live server sessions.
- [ ] Validate server stability with Astron local launcher under heavy zone switching.

