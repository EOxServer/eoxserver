class PolicyDecisionPointInterface(object):
    """ This is the interface for Policy Decision Point (PDP) implementations.
    """

    @property
    def pdp_type(self):
        """ The type name of this PDP.
        """

    def authorize(self, request):
        """ This method takes an :class:`~.OWSRequest` object as input and returns an
            :class:`~.AuthorizationResponse` instance. It is expected to check if
            the authenticated user (if any) is authorized to access the requested
            resource and set the ``authorized`` flag of the response accordingly.

            In case the user is not authorized, the content and status of the
            response shall be filled with an error message and the appropriate
            HTTP Status Code (403).

            The method shall not raise any exceptions.
        """
