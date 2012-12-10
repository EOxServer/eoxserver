#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

from django.db.models import Q

from eoxserver.core.system import System
from eoxserver.resources.coverages.exceptions import (
    ManagerError, CoverageIdReservedError,
    CoverageIdInUseError, CoverageIdReleaseError ) 
from eoxserver.resources.coverages.models import (
    PlainCoverageRecord, RectifiedDatasetRecord, 
    ReferenceableDatasetRecord, RectifiedStitchedMosaicRecord,
    ReservedCoverageIdRecord, CoverageRecord, DatasetSeriesRecord,
) 

try:
    from django.utils import timezone
except ImportError:
    from datetime import datetime as timezone
from datetime import timedelta

#-------------------------------------------------------------------------------

#COVERAGE_TYPES = { 
#        "PlainCoverage" : PlainCoverageRecord ,
#        "RectifiedDataset" : RectifiedDatasetRecord , 
#        "ReferenceableDataset" : ReferenceableDatasetRecord , 
#        "RectifiedStitchedMosaic" : RectifiedStitchedMosaicRecord ,
#}

COVERAGE_EO_TYPES = { 
        "RectifiedDataset" : RectifiedDatasetRecord , 
        "ReferenceableDataset" : ReferenceableDatasetRecord , 
        "RectifiedStitchedMosaic" : RectifiedStitchedMosaicRecord ,
} 
    
#EO_TYPES = { 
#        "RectifiedDataset" : RectifiedDatasetRecord , 
#        "ReferenceableDataset" : ReferenceableDatasetRecord , 
#        "RectifiedStitchedMosaic" : RectifiedStitchedMosaicRecord ,
#        "DatasetSeries" : DatasetSeriesRecord ,
#}

#-------------------------------------------------------------------------------

class CoverageIdManager(object):
    """
    Manager for Coverage IDs. The purpose of this manager class is to help: 

        * During registration of a new EO-entities/coverage when the uniqueness
          of the ID must be guarantied. Further, the manager provies means for
          time limitted reservation (booking) of IDs preventing any parallel 
          process to ``steal`` the ID while the new coverage is being
          registered. 

        * During inspection of an existing ID. The manager determines wehther
          the inspected ID belongs to an existing EO-entity/coverage or is
          reserved for a new one. Further, it helps to determine type of the
          EO-entity/coverage associated to it so that a proper specific manager
          class can be selected for further action. 

    .. note:: 
        
        EOIDs of DatasetSeries are now included. The name ``CoverageIdManager``
        is therefore misleading as the EO-IDs are involved in the checks. 

    """
    
    def reserve(self, coverage_id, request_id=None, until=None):
        """
        Tries to reserve a ``coverage_id`` until a given datetime. If ``until``
        is omitted, the configuration value 
        ``resources.coverages.coverage_id.reservation_time`` is used.
        
        If the ID is already reserved and the ``resource_id`` is not equal to
        the reserved ``resource_id``, a :class:`~.CoverageIdReservedError` is
        raised. If the ID is already taken by an existing coverage a 
        :class:`~.CoverageIdInUseError` is raised.
        These exceptions are sub-classes of :exc:`~.CoverageIdError`.
        """
        
        obj, _ = ReservedCoverageIdRecord.objects.get_or_create(
            coverage_id=coverage_id,
            defaults={
                "until": timezone.now()
            }
        )
        
        if not until:
            values = System.getConfig().getConfigValue(
                "resources.coverages.coverage_id", "reservation_time"
            ).split(":")
            
            for _ in xrange(len(values[:4]) - 4):
                values.insert(0, 0)
            
            dt = timedelta(days=int(values[0]), hours=int(values[1]),
                           minutes=int(values[2]), seconds=int(values[3]))
            until = timezone.now() + dt
        
        if timezone.now() < obj.until:
            if not (obj.request_id == request_id and obj.request_id is not None):
                raise CoverageIdReservedError(
                    "Coverage ID '%s' is reserved until %s" % (coverage_id, obj.until)
                )
        elif CoverageRecord.objects.filter(coverage_id=coverage_id).count() > 0:
            raise CoverageIdInUseError("Coverage ID '%s' is already in use."
                % coverage_id
            )
        
        obj.request_id = request_id
        obj.until = until
        obj.save()

        
    def release(self, coverage_id, fail=False):
        """
        Releases a previously reserved ``coverage_id``.
        
        If ``fail`` is set to ``True``, an exception is raised when the ID was 
        not previously reserved.
        """
        
        try: 
            obj = ReservedCoverageIdRecord.objects.get(coverage_id=coverage_id)
            obj.delete()
            
        except ReservedCoverageIdRecord.DoesNotExist:
            if fail:
                raise CoverageIdReleaseError(
                    "Coverage ID '%s' was not reserved" % coverage_id
                )

    
    def check( self , coverage_id ): 
        """ 

        .. warning:: 

            This method has been deprecated. Use :meth:`isUsed` instead.

        """
        return self.isUsed( coverage_id ) 


    def isUsed( self , coverage_id ) : 
        """
        Returns a boolean value, indicating if the ``coverage_id`` is identifier
        of an existing entity (coverage, eo-dataset, rs-mosaic or ds-series).  

        .. note:: 

            The check also involves EO-IDs!

        """

        # TODO unify the coverage and eo IDs!!!
        count  = CoverageRecord.objects.filter(coverage_id=coverage_id).count()
        count += RectifiedDatasetRecord.objects.filter(eo_id=coverage_id).count()
        count += ReferenceableDatasetRecord.objects.filter(eo_id=coverage_id).count()
        count += RectifiedStitchedMosaicRecord.objects.filter(eo_id=coverage_id).count()
        count += DatasetSeriesRecord.objects.filter(eo_id=coverage_id).count() 

        return ( count > 0 ) 


    def isReserved( self , coverage_id ) : 
        """
        Returns a boolean value, indicating if the ``coverage_id`` is reserved
        for an entity being currently created. 
        """

        return ( ReservedCoverageIdRecord.objects.filter(coverage_id=\
                coverage_id,until__gte=timezone.now()).count() > 0 )


    def getCoverageType( self , coverage_id ):
        """ 

        .. warning:: 

            This method has been deprecated. Use :meth:`getType` instead.

        """
        return self.getType( coverage_id ) 


    def getType( self , coverage_id ): 
        """
        Returns string, type name of the entity identified by the given ID.
        In case there is no entity corresponding to the given ID None is
        returned.

        Possible return values are:
            None, 'PlainCoverage', 'RectifiedDataset', 'ReferenceableDataset',
            'RectifiedStitchedMosaic', 'DatasetSeries', and 'Reserved'
        """

        #TODO: There should be a fast and easy method how to get the coverage/series type!
        #      If possible in a SINGLE DB query.

        for ct in COVERAGE_EO_TYPES : 
            if COVERAGE_EO_TYPES[ct].objects.filter( 
                    Q(coverage_id=coverage_id) | Q(coverage_id=coverage_id)
                ).count() > 0 : return ct 

        if DatasetSeriesRecord.objects.filter(eo_id=coverage_id).count() > 0 : 
            return "DatasetSeries"

        if PlainCoverageRecord.objects.filter(coverage_id=coverage_id).count() > 0 : 
            return "PlainCoverage" 

        if self.isReserved( coverage_id ) : 
            return "Reserved" 

        return None 


    def available(self, coverage_id): # TODO available for a specific request_id
        """ 

        .. warning:: 

            This method has been deprecated. Use :meth:`isAvailable` instead.

        """
        return self.isAvailable(coverage_id)


    def isAvailable(self, coverage_id): # TODO available for a specific request_id
        """
        Returns a boolean value, indicating if the ``coverage_id`` is identifier
        of an existing entity (coverage, eo-dataset, rs-mosaic or ds-series)
        or it is a reserved ID. 

        .. note:: 

            The check also involves EO-IDs!

        """
        return not ( self.isReserved(coverage_id) or self.isUsed(coverage_id) )  

    
    def getRequestId(self, coverage_id):
        """
        Returns the request ID associated with a 
        :class:`~.ReservedCoverageIdRecord` or `None` if the no record with that
        ID is available.
        """
        
        try:
            obj = ReservedCoverageIdRecord.objects.get(coverage_id=coverage_id)
            return obj.request_id
        except ReservedCoverageIdRecord.DoesNotExist:
            return None

        
    def getCoverageIds(self, request_id):
        """ 

        .. warning:: 

            This method has been deprecated. Use :meth:`getReservedIds`
            instead.

        """
        return self.getReservedIds(request_id) 


    def getReservedIds(self, request_id):
        """
        Returns a list of all reserved IDs associated to a specific request ID.
        """
        return [ obj.coverage_id for obj in ReservedCoverageIdRecord.\
                    objects.filter(request_id=request_id) ]

    def getAllReservedIds(self):
        """
        Returns a list of all reserved IDs associated to a specific request ID.
        """
        return [ obj.coverage_id for obj in ReservedCoverageIdRecord.\
                    objects.all() ]


    #def _get_id_factory(self):
    #    # Unused, but would raise an exception.
    #    return None

#-------------------------------------------------------------------------------
