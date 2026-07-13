"""
AssetCache - Preloads and caches common assets for instant zone loading
"""
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
        """Preload common assets used across all zones"""
        if self._initialized:
            return
            
        self.notify.info('Preloading common assets for faster zone loading...')
        
        # Common models that are used everywhere
        commonModels = [
            'phase_3/models/props/arrow',
            'phase_3/models/props/panel',
            'phase_3/models/props/chatbox',
            'phase_3/models/props/chatbox_noarrow',
            'phase_3/models/gui/chat_button_gui',
            'phase_3/models/misc/sphere',
        ]
        
        # Preload models asynchronously
        for modelPath in commonModels:
            try:
                model = loader.loadModel(modelPath)
                if model:
                    self.preloadedModels[modelPath] = model
                    # Keep in model pool
                    ModelPool.addModel(modelPath, model.node())
            except:
                pass
        
        # Texture and Model pools manage their own sizes automatically
        # Just ensure they're enabled for caching
        
        self._initialized = True
        self.notify.info('Asset preloading complete')
    
    def cleanup(self):
        """Clean up cached assets"""
        self.preloadedModels.clear()
        self.preloadedTextures.clear()
        self.preloadedSounds.clear()
        self.preloadedMusic.clear()
        self._initialized = False
        
    def getModel(self, modelPath):
        """Get a preloaded model if available"""
        return self.preloadedModels.get(modelPath)


# Global instance
assetCache = AssetCache.getInstance()

