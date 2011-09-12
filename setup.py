from distutils.core import setup

packages=['volumeeditor', 
          'volumeeditor.pixelpipeline',
          'volumeeditor.colorama',
          'volumeeditor.layerwidget',
          'volumeeditor.view3d',
          'volumeeditor.resources',
          'volumeeditor.resources.icons']

package_data={'volumeeditor.resources.icons': ['*.png', 'LICENSES']}

setup(name='volumeeditor',
      version='0.6a',
      description='Volume Slicer and Editor',
      url='https://github.com/Ilastik/volumeeditor',
      packages=packages,
      package_data=package_data
     )
