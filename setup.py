from distutils.core import setup

setup(
    name='garage',
    version='v0.0.0a1',
    packages=[''],
    package_dir={'': 'garage'},
    install_requires=['nanpy','cherrypy'],
    url='https://github.com/mitainesoft/garage',
    license='Mitainesoft Garage 2017',
    python_requires='~=3.3',
    author='mitainesoft',
    author_email='mitainesoft@gmail.com',
    description='Supervise garage door opening. Generate alarms in UI and by emails. Works on raspberry pi with Arduino Uno board.'
)
