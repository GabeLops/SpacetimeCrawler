'''
Created on Oct 20, 2016
@author: Rohan Achar
'''
from rtypes.pcc.attributes import dimension, primarykey, predicate
from rtypes.pcc.types.subset import subset
from rtypes.pcc.types.set import pcc_set
from rtypes.pcc.types.projection import projection
from rtypes.pcc.types.impure import impure
from datamodel.search.server_datamodel import Link, ServerCopy

@pcc_set
class GlopsLink(Link):
    USERAGENTSTRING = "Glops"

    @dimension(str)
    def user_agent_string(self):
        return self.USERAGENTSTRING

    @user_agent_string.setter
    def user_agent_string(self, v):
        # TODO (rachar): Make it such that some dimensions do not need setters.
        pass


@subset(GlopsLink)
class GlopsUnprocessedLink(object):
    @predicate(GlopsLink.download_complete, GlopsLink.error_reason)
    def __predicate__(download_complete, error_reason):
        return not (download_complete or error_reason)


@impure
@subset(GlopsUnprocessedLink)
class OneGlopsUnProcessedLink(GlopsLink):
    __limit__ = 1

    @predicate(GlopsLink.download_complete, GlopsLink.error_reason)
    def __predicate__(download_complete, error_reason):
        return not (download_complete or error_reason)

@projection(GlopsLink, GlopsLink.url, GlopsLink.download_complete)
class GlopsProjectionLink(object):
    pass
