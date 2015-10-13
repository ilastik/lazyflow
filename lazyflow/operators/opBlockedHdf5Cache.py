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
#          http://ilastik.org/license/
###############################################################################

import copy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import RamMeasurementContext

from opCacheFixer import OpCacheFixer
from opUnblockedHdf5Cache import OpUnblockedHdf5Cache
from opSplitRequestsBlockwise import OpSplitRequestsBlockwise

class OpBlockedHdf5Cache(Operator):
    """
    A blockwise array cache, similar to OpBlockedArrayCache, but all data is stored in an open HDF5 group,
    not in numpy arrays.  
    Instead of a monolithic implementation, this operator is a small pipeline of three simple operators.
    
    The actual caching of data is handled by an unblocked cache, so the "blocked" functionality is 
    implemented via separate "splitting" operator that comes after the cache.
    Also, the "fixAtCurrent" feature is implemented in a special operator, which comes before the cache.    
    """
    fixAtCurrent = InputSlot(value=False)
    Input = InputSlot()
    H5CacheGroup = InputSlot()
    #BlockShape = InputSlot()
    innerBlockShape = InputSlot(optional=True)
    outerBlockShape = InputSlot()
    
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super( OpBlockedHdf5Cache, self ).__init__(*args, **kwargs)
        
        # Input ---------> opCacheFixer -> opUnblockedHdf5Cache -> opSplitRequestsBlockwise -> Output
        #                 /               /                        /
        # fixAtCurrent ---               /                        /
        #                               /                        /
        # H5CacheGroup -----------------                        /
        #                                                      /
        # BlockShape ------------------------------------------
        
        self._opCacheFixer = OpCacheFixer( parent=self )
        self._opCacheFixer.Input.connect( self.Input )
        self._opCacheFixer.fixAtCurrent.connect( self.fixAtCurrent )

        self._opUnblockedHdf5Cache = OpUnblockedHdf5Cache( None, parent=self )
        self._opUnblockedHdf5Cache.Input.connect( self._opCacheFixer.Output )
        self._opUnblockedHdf5Cache.H5CacheGroup.connect( self.H5CacheGroup )

        self._opSplitRequestsBlockwise = OpSplitRequestsBlockwise( always_request_full_blocks=True, parent=self )
        self._opSplitRequestsBlockwise.BlockShape.connect( self.outerBlockShape )
        self._opSplitRequestsBlockwise.Input.connect( self._opUnblockedHdf5Cache.Output )

        self.Output.connect( self._opSplitRequestsBlockwise.Output )

    def setupOutputs(self):
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass
