from setuptools import setup

setup(name='facebook_downloader',
      version='0.1',
      description='API wrapper and crawler to download page posts from the Facebook Graph API',
      url='http://github.com/coej/facebook_downloader',
      author='Chris Jenkins',
      author_email='chrisoej@gmail.com',
      license='MIT',
      packages=['facebook_downloader'],
      install_requires=[
          'pymongo',
          'requests',
          'future',
          
      ],
      # dependency_links=['http://github.com/user/repo/tarball/master#egg=package-1.0']
      # for stuff not on pypi

      include_package_data=True,
      # use this if I want to copy over things in MANIFEST.in when installing

      zip_safe=False)