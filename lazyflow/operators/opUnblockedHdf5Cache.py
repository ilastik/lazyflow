###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#           http://ilastik.org/license/
###############################################################################

import time
import collections
import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.request import RequestLock
from lazyflow.roi import getIntersection, roiFromShape, roiToSlice, containing_rois

import logging
logger = logging.getLogger(__name__)

class OpUnblockedHdf5Cache(Operator):
    """
    This cache operator stores the results of all requests that pass through 
    it, in exactly the same blocks that were requested.

    - If there are any overlapping requests, then the data for the overlapping portion will 
        be stored multiple times, except for the special case where the new request happens 
        to fall ENTIRELY within an existing block of data.
    - If any portion of a stored block is marked dirty, the entire block is discarded.

    Unlike other caches, this cache does not impose its own blocking on the data.
    Instead, it is assumed that the downstream operators have chosen some reasonable blocking.
    Hopefully the downstream operators are reasonably consistent in the blocks they request data with,
    since every unique result is cached separately.
    """
    Input = InputSlot()
    H5CacheGroup = InputSlot()
    Output = OutputSlot()
    
    def __init__(self, dataset_kwargs, *args, **kwargs):
        super( OpUnblockedHdf5Cache, self ).__init__(*args, **kwargs)
        self._lock = RequestLock()
        self._h5group = None
        dataset_kwargs = dataset_kwargs or { 'compression' : 'lzf' }
        self._dataset_kwargs = dataset_kwargs
        self._block_locks = {}

    @classmethod
    def _standardize_roi(cls, start, stop):
        # We use rois as dict keys.
        # For comparison purposes, all rois in the dict keys are assumed to be tuple-of-tuples-of-int
        start = tuple(map(int, start))
        stop = tuple(map(int, stop))        
        return (start, stop)

    @classmethod
    def roi_str(cls, start, stop):
        roi = cls._standardize_roi(start, stop)
        return str(roi_str)

    def setupOutputs(self):
        with self._lock:
            self._h5group = self.H5CacheGroup.value
        self.Output.meta.assignFrom(self.Input.meta)
    
    def _clear_blocks(self):
        keys = self._h5group.keys()
        for k in keys:
            del self._h5group[k]
        self._block_locks = {}

    def execute(self, slot, subindex, roi, result):
        with self._lock:
            # Does this roi happen to fit ENTIRELY within an existing stored block?
            block_rois = map( eval, self._h5group.keys() )
            outer_rois = containing_rois( block_rois, (roi.start, roi.stop) )
            if len(outer_rois) > 0:
                # Use the first one we found
                block_roi = self._standardize_roi( *outer_rois[0] )
                block_relative_roi = numpy.array( (roi.start, roi.stop) ) - block_roi[0]
                
                self.Output.stype.copy_data(result, self._h5group[str(block_roi)][ roiToSlice(*block_relative_roi) ])
                return
                
        # Standardize roi for usage as dict key
        block_roi = self._standardize_roi( roi.start, roi.stop )
        
        # Get lock for this block (create first if necessary)
        with self._lock:
            if block_roi not in self._block_locks:
                self._block_locks[block_roi] = RequestLock()
            block_lock = self._block_locks[block_roi]

        # Handle identical simultaneous requests
        with block_lock:
            if str(block_roi) in self._h5group:
                self.Output.stype.copy_data(result, self._h5group[str(block_roi)])
                return
            else: # Not yet stored: Request it now.
                # We attach a special attribute to the array to allow the upstream operator
                #  to optionally tell us not to bother caching the data.
                self.Input(roi.start, roi.stop).writeInto(result).block()

                if self.Input.meta.dontcache:
                    # The upstream operator says not to bother caching the data.
                    # (For example, see OpCacheFixer.)
                    return
                
                with self._lock:
                    # Store the data.
                    # First double-check that the block wasn't removed from the 
                    #   cache while we were requesting it. 
                    # (Could have happened via propagateDirty() or eventually the arrayCacheMemoryMgr)
                    if block_roi in self._block_locks:
                        self._h5group.create_dataset( str(block_roi),
                                                      data=result,
                                                      **self._dataset_kwargs )

    def propagateDirty(self, slot, subindex, roi):
        dirty_roi = self._standardize_roi( roi.start, roi.stop )
        maximum_roi = roiFromShape(self.Input.meta.shape)
        maximum_roi = self._standardize_roi( *maximum_roi )
        
        if dirty_roi == maximum_roi:
            # Optimize the common case:
            # Everything is dirty, so no need to loop
            self._clear_blocks()
        else:
            # FIXME: This is O(N) for now.
            #        We should speed this up by maintaining a bookkeeping data structure in execute().
            for block_roi_str in self._h5group.keys():
                block_roi = eval(block_roi_str)
                if getIntersection(block_roi, dirty_roi, assertIntersect=False):
                    del self._h5group[block_roi_str]

        self.Output.setDirty( roi.start, roi.stop )
