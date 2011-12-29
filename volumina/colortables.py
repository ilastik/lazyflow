'''Colortables.

Colortables map from raw pixel values to colors and are stored as a
list of QRgb values. The list indices are interpreted as the raw
values.

Example:
colortable = [QColor(Qt.Red).rgba(), QColor(Qt.Black).rgba()]

This table is applicable to raw with two different values 0 and 1. 0s
will be displayed red and 1s black.

'''

import itertools
from PyQt4.QtGui import QColor

default16 = [QColor(0, 0, 255).rgba(),
            QColor(255, 255, 0).rgba(),
            QColor(255, 0, 0).rgba(),
            QColor(0, 255, 0).rgba(),
            QColor(0, 255, 255).rgba(),
            QColor(255, 0, 255).rgba(),
            QColor(255, 105, 180).rgba(), #hot pink
            QColor(102, 205, 170).rgba(), #dark aquamarine
            QColor(165,  42,  42).rgba(), #brown        
            QColor(0, 0, 128).rgba(),     #navy
            QColor(255, 165, 0).rgba(),   #orange
            QColor(173, 255,  47).rgba(), #green-yellow
            QColor(128,0, 128).rgba(),    #purple
            QColor(192, 192, 192).rgba(), #silver
            QColor(240, 230, 140).rgba(), #khaki
            QColor(69, 69, 69).rgba()]    # dark grey


def create_default_16bit():
    '''Create a colortable suitable for 16bit data.

    Repeatedly applies the default16 colortable to the whole 16bit range.
    
    '''
    return [color for color in itertools.islice(itertools.cycle(default16), 0, 2**16)]
