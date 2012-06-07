from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup

@onsetup
def setup_product():
    fiveconfigure.debug_mode = True
    import tn.plonehtmlimagecache
    zcml.load_config('configure.zcml', tn.plonehtmlimagecache)
    fiveconfigure.debug_mode = False

setup_product()
ptc.setupPloneSite(products=['tn.plonehtmlimagecache'])

class TestCase(ptc.PloneTestCase):
    pass
