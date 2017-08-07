#from distutils.core import setup
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
from glob import glob
import time
import datetime
import os
import sys
import traceback
import configparser
import subprocess

current_dir = path.abspath(path.dirname(__file__))
package_outfiles = current_dir +"/packages"

# Get the long description from the README file
with open(path.join(current_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

nowstr=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
print ("current build time=%s\n" % nowstr)


buildfilename       = current_dir + "/build_info.txt"
print("Build info filename:%s" % (buildfilename))

try:
    with open(buildfilename) as f:
        f.close()
except IOError:
    print("Config file " + buildfilename + " does not exist ! ")
    print("Exiting...")
    os._exit(-1)

buildinfo = configparser.ConfigParser()
buildinfo.read(buildfilename)

print ("Garage current version = %s.%s.%s" %(buildinfo['BUILDINFO']['mgs.major'],buildinfo['BUILDINFO']['mgs.minor'],buildinfo['BUILDINFO']['mgs.patch']))

major=int(buildinfo['BUILDINFO']['mgs.major'])
minor = int(buildinfo['BUILDINFO']['mgs.minor'])
patch=int(buildinfo['BUILDINFO']['mgs.patch'])+1

#print ("Garage next version %s.%s.%s" %(major,minor,patch))

buildinfo['BUILDINFO']['build.date'] = nowstr
buildinfo['BUILDINFO']['mgs.major'] = "%d" % major
buildinfo['BUILDINFO']['mgs.minor'] = "%d" % minor
buildinfo['BUILDINFO']['mgs.patch'] = "%d" % patch
print ("Garage next version = %s.%s.%s" %(buildinfo['BUILDINFO']['mgs.major'],buildinfo['BUILDINFO']['mgs.minor'],buildinfo['BUILDINFO']['mgs.patch']))

with open(buildfilename, 'w') as buildinfofile:
    buildinfo.write(buildinfofile)


version_str = "v%s.%s.%s" %(buildinfo['BUILDINFO']['mgs.major'],buildinfo['BUILDINFO']['mgs.minor'],buildinfo['BUILDINFO']['mgs.patch'])
package_name="mitainesoft_garage_"+version_str

print ("GIT Pull, Commit & Push $buildfile... \n")

vcscmd_array =  [["git" ,"status"],
                ["git" ,"pull"],
                ["git", "commit", "-n", "-m", package_name, buildfilename],
                ["git", "status"],
                ["git", "push"]]

for i in range (len(vcscmd_array)):
    print ("%d) VCS cmd=%s" % (i,vcscmd_array[i]))
    outstr=subprocess.call (vcscmd_array[i])

#os._exit(-1)

setup(
    name='mitainesoft_garage',
    version=version_str,
    packages=find_packages(),
    include_package_data=True,
#    package_dir=package_outfiles,
#    script_args='dist-dir=allo',
    install_requires=['nanpy','cherrypy'],
    url='https://github.com/mitainesoft/garage',
    license='Mitainesoft Garage 2017',
    python_requires='~=3.3',
    author='mitainesoft',
    author_email='mitainesoft@gmail.com',
    description='Monitor and Control Garage Door',
    long_description='Supervise garage door opening. Generate Alarms if required.  Allow remote open. Security via certificates and other fireall options. SCRUM board: https://github.com/mitainesoft/garage/projects',
    platforms='Raspberry PI armv7l GNU/Linux 4.9.28-v7+',
)

