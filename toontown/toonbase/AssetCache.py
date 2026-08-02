from direct.directnotify.DirectNotifyGlobal import directNotify
from panda3d.core import ModelPool, TexturePool, NodePath


class AssetCache:
    notify = directNotify.newCategory('AssetCache')
    _instance = None
    
    def __init__(self):
        self.preloadedModels = {}
        self.preloadedTextures = {}
        self.preloadedSounds = {}
        self.preloadedMusic = {}
        self._initialized = False
        
    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = AssetCache()
        return cls._instance
    
    def initialize(self, loader):
        if self._initialized:
            return
            
        self.notify.info('Preloading common assets for faster zone loading...')
        
        commonModels = [
            'phase_3/models/gui/toontown-logo',
            'phase_3/models/gui/tt_m_gui_ups_logo_noText',
            'phase_3/models/gui/progress-background',
            'phase_3/models/gui/dialog_box_gui',
            'phase_3/models/gui/quit_button',
            'phase_3/models/props/arrow',
            'phase_3/models/props/panel',
            'phase_3/models/props/chatbox',
            'phase_3/models/props/chatbox_noarrow',
            'phase_3/models/gui/chat_button_gui',
            'phase_3/models/misc/sphere',
            'phase_3.5/models/props/drop_shadow',
            'phase_3.5/models/gui/inventory_icons',
        ]
        
        for modelPath in commonModels:
            try:
                model = loader.loadModel(modelPath, okMissing=True)
                if model:
                    self.preloadedModels[modelPath] = model
                    ModelPool.addModel(modelPath, model.node())
            except Exception:
                pass
        
        self._initialized = True
        self.notify.info('Asset preloading complete')
    
    def cleanup(self):
        self.preloadedModels.clear()
        self.preloadedTextures.clear()
        self.preloadedSounds.clear()
        self.preloadedMusic.clear()
        self._initialized = False
        
    def getModel(self, modelPath):
        return self.preloadedModels.get(modelPath)


assetCache = AssetCache.getInstance()
