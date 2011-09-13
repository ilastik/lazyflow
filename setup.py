from distutils.core import setup

packages=['volumina', 
          'volumina.pixelpipeline',
          'volumina.colorama',
          'volumina.layerwidget',
          'volumina.view3d',
          'volumina.resources',
          'volumina.resources.icons']

package_data={'volumina.resources.icons': ['*.png', 'LICENSES']}

setup(name='volumina',
      version='0.6a',
      description='Volume Slicer and Editor',
      url='https://github.com/Ilastik/volumina',
      packages=packages,
      package_data=package_data
     )
