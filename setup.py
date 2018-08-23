import re
from setuptools import setup, Command
import os
from pip.req import parse_requirements


def get_requirements():
    pth = os.path.join(os.path.dirname(__file__), 'REQUIREMENTS')
    install_reqs = parse_requirements(pth, session='setup_hack')
    res = [str(ir.req) for ir in install_reqs
            if str(ir.req) != "None"]
    return res


with open('adsocket/version.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)


class TeamCityVersionCommand(Command):

    description = "Report package version to TeamCity"
    user_options = []

    def initialize_options(self):
        """NOOP"""
        pass

    def finalize_options(self):
        """NOOP"""
        pass

    def run(self):
        """
        Echo the teamcity service message
        """
        print(
            "##teamcity[buildNumber '{}-{{build.number}}']"
            .format(version)
        )


setup(
    name="adsocket",
    cmdclass={
        'tc_version': TeamCityVersionCommand
    },
    install_requires=get_requirements(),
    packages=['adsocket'],
    zip_safe=True,
    include_package_data=True,
    platforms='any',
    license='MIT',
    description="Websocket protocol",
    version=version
)
