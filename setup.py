from distutils.core import setup
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='garage',
    version='v0.0.0a1',
    packages=['GarageFrontend'],
    package_data={'': ['doc','config','GarageBackend'],},
    install_requires=['nanpy','cherrypy'],
    url='https://github.com/mitainesoft/garage',
    license='Mitainesoft Garage 2017',
    python_requires='~=3.3',
    author='mitainesoft',
    author_email='mitainesoft@gmail.com',
    description='Supervise garage door opening. Generate alarms in UI and by emails. Works on raspberry pi with Arduino Uno board.'
)

