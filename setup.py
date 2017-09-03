# from distutils.core import setup
from setuptools import setup, find_packages
import setuptools.command.build_py
import setuptools.command.sdist
import distutils.cmd
import distutils.log
# import setuptools
import subprocess

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
from tempfile import mkstemp
from shutil import move
from os import fdopen, remove
import codecs

fileListToSearchReplace_MITAINESOFT_GARAGE_REVISION = \
    ['README.rst',
     'GarageFrontend/index.html',
     'config/garage_backend.template']

current_dir = path.abspath(path.dirname(__file__))
package_outfiles = current_dir + "/packages"

# Get the long description from the README file
with open(path.join(current_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

nowstr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
print("current build time=%s\n" % nowstr)

pre_vcscmd_array = [["git", "status"], ["git", "pull"]]
for j in range(len(pre_vcscmd_array)):
    print("%d) Pre-Build VCS cmd=%s" % (j, pre_vcscmd_array[j]))
    subprocess.call (pre_vcscmd_array[j])

buildfilename = current_dir + "/build_info.txt"
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

print("Garage current version = %s.%s.%s" % (buildinfo['BUILDINFO']['mgs.major'], buildinfo['BUILDINFO']['mgs.minor'], buildinfo['BUILDINFO']['mgs.patch']))

major = int(buildinfo['BUILDINFO']['mgs.major'])
minor = int(buildinfo['BUILDINFO']['mgs.minor'])
patch = int(buildinfo['BUILDINFO']['mgs.patch']) + 1

# print ("Garage next version %s.%s.%s" %(major,minor,patch))

buildinfo['BUILDINFO']['build.date'] = nowstr
buildinfo['BUILDINFO']['mgs.major'] = "%d" % major
buildinfo['BUILDINFO']['mgs.minor'] = "%d" % minor
buildinfo['BUILDINFO']['mgs.patch'] = "%d" % patch
print("Garage next version = %s.%s.%s" % (buildinfo['BUILDINFO']['mgs.major'], buildinfo['BUILDINFO']['mgs.minor'], buildinfo['BUILDINFO']['mgs.patch']))

with open(buildfilename, 'w') as buildinfofile:
    buildinfo.write(buildinfofile)

version_str = "v%s.%s.%s" % (buildinfo['BUILDINFO']['mgs.major'], buildinfo['BUILDINFO']['mgs.minor'], buildinfo['BUILDINFO']['mgs.patch'])
package_name = "mitainesoft_garage_" + version_str

print("GIT Pull, Commit & Push $buildfile... \n")

vcscmd_array = [["git", "status"],
                ["git", "pull"],
                ["git", "commit", "-n", "-m", package_name, buildfilename],
                ["git", "status"],
                ["git", "push"]]

for i in range(len(vcscmd_array)):
    print("%d) VCS cmd=%s" % (i, vcscmd_array[i]))
    subprocess.call (vcscmd_array[i])


# os._exit(-1)


# class BuildPyCommand(setuptools.command.build_py.build_py):
#     """Custom build command."""
#     print(setuptools.command.build_py.build_py.__name__)
#     command = ['find', '.', '-name', 'index.html', '-ls']
#     print("\nBuildPyCommand cmd=%s \n\n %s\n" % (command, os.getcwd()))
#     subprocess.check_call(command)
#
#
#     def run(self):
#         print("BuildPyCommand run:" + __name__)
#         self.run_command('stuff')
#         setuptools.command.build_py.build_py.run(self)
#         exit(-1)


class sdistPyCommand(setuptools.command.sdist.sdist):
    """Custom build command."""
    # print(setuptools.command.sdist.sdist.__name__)
    # command = ['find', '.', '-name', 'index.html', '-ls']
    # print("\nsdistPyCommand cmd=%s \n\n %s\n" % (command, os.getcwd()))
    # subprocess.check_call(command)
    # exit(-2)

    def run(self):
        # print("sdistPyCommand run ENTRY:" + __name__)
        # self.run_command('stuff')
        setuptools.command.sdist.sdist.run(self)
        # print("sdistPyCommand run EXIT:" + __name__)

    def make_distribution(self):
        # print("sdistPyCommand make_distribution ENTRY:" + __name__)
        # self.run_command('stuff')
        setuptools.command.sdist.sdist.make_distribution(self)
        # print("sdistPyCommand make_distribution EXIT:" + __name__)

    def make_release_tree(self,base_dir, files ):
        # print("sdistPyCommand make_release_tree ENTRY:" + __name__)
        # self.run_command('stuff')
        setuptools.command.sdist.sdist.make_release_tree(self,base_dir, files)

        for fileToSearchReplace in fileListToSearchReplace_MITAINESOFT_GARAGE_REVISION:
            try:
                source_file_path=base_dir+'/'+fileToSearchReplace
                keyw='[MITAINESOFT_GARAGE_REVISION]'
                substring = base_dir.upper()
                if (fileToSearchReplace == "README.rst"): #Exception for instructions, not upper() !
                    substring = base_dir
                print("File: "+fileToSearchReplace+"   search: "+keyw+"   replace with: "+substring)
                self.replace(source_file_path,keyw,substring)
            except Exception:
                print ("Error for file:"+fileToSearchReplace)
                traceback.print_exc()
                os._exit(-5)
        # print("sdistPyCommand make_release_tree EXIT:" + __name__)

    def replace(self,source_file_path, pattern, substring):
        fh, target_file_path = mkstemp()

        with codecs.open(target_file_path, 'w', 'utf-8') as target_file:
            with codecs.open(source_file_path, 'r', 'utf-8') as source_file:
                for line in source_file:
                    target_file.write(line.replace(pattern, substring))
        remove(source_file_path)
        move(target_file_path, source_file_path)

setuptools.setup(
    cmdclass={
        # 'stuff': PylintCommand,
        # 'build_py': BuildPyCommand,
        'sdist': sdistPyCommand,
    },
    name='garage',
    version=version_str,
    packages=find_packages(),
    include_package_data=True,
    install_requires=['nanpy', 'cherrypy'],
    url='https://github.com/mitainesoft/garage',
    license='Mitainesoft Garage 2017',
    python_requires='~=3.3',
    author='mitainesoft',
    author_email='mitainesoft@gmail.com',
    description='Monitor and Control Garage Door',
    long_description='Supervise garage door opening. Generate Alarms if required.  Allow remote open. Security via certificates and other fireall options. SCRUM board: https://github.com/mitainesoft/garage/projects',
    platforms='Raspberry PI armv7l GNU/Linux 4.9.28-v7+',
)
