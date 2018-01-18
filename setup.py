from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pyUtilities',
      version='0.1',
      description='Utility functions and 3rd party integrations',
      long_description=readme(),
      url='https://github.com/stikks/Utilities',
      author='stikks && kunsam002',
      author_email='styccs@gmail.com',
      include_package_data=True,
      packages=find_packages(),
      install_requires=[
          'requests',
          'tablib',
          'phonenumbers',
          'user-agents',
          'pymongo',
          'influxdb',
          'pygeocoder',
          'htmlmin',
          'pillow',
          'pyaes',
          'cryptography'
      ])