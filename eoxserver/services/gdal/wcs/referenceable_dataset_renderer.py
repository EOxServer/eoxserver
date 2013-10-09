
class ReferenceableDatasetRenderer(Component):
    implements(WCSCoverageRendererInterface)
    handles = (models.ReferenceableDataset,)

    def render(self, coverage, parameters):
        pass
