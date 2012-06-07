from five.intid.site import addUtility
from tn.plonehtmlimagecache import interfaces
from tn.plonehtmlimagecache.caching import Cache
from tn.plonehtmlimagecache.context_keys import ContextKeys


CONTEXT_KEYS_ID = 'tn.bulletino.context_keys'
CACHE_ID        = 'tn.bulletino.cache'

def installUtilities(context):
    if context.readDataFile('tn.plonehtmlimagecache-install-utilities.txt') is None:
        return

    portal = context.getSite()
    addUtility(portal, interfaces.IContextKeys, ContextKeys,
               ofs_name=CONTEXT_KEYS_ID, findroot=False)
    addUtility(portal, interfaces.ICache, Cache,
               ofs_name=CACHE_ID, findroot=False)
