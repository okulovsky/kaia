from unittest import TestCase
from kaia.app import KaiaAppSettings, KaiaApp
from foundation_kaia.misc import Loc
from avatar.messaging.amenities.graph_building import *
from avatar.daemon import *

class RulesDrawingsTestCase(TestCase):
    def test_rules_drawings(self):
        settings = KaiaAppSettings()
        app = KaiaApp(Loc.data_folder/'demo')
        app.brainbox_api = 'exists'
        settings.avatar_processor.bind_app(app)
        rules = app.avatar_processor.rules.rules

        builder = GraphBuilder(
            rules,
            (UtteranceSequenceCommand, TextCommand),
            (),
            ('NarrationService',)
        )
        builder.build()
        g = render_rules_graph(builder)
        g.render(filename="rules_graph", format="png", cleanup=True)


