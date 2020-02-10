import re
from setuptools import setup, Command, find_packages


def get_requirements():
    req = []
    deps = []
    with open("REQUIREMENTS", "r") as f:
        for l in  f.readlines():
            l = l.strip()
            if l.startswith("#"):
                continue
            elif l.startswith("git+"):
                deps.append(l)
            else:
                req.append(l)
    return req, deps


reqs, deps = get_requirements()

with open('adsocket/version.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)


with open("README.md", "r") as fh:
    long_description = fh.read()


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
    install_requires=reqs,
    dependency_links=deps,
    packages=find_packages(),
    zip_safe=True,
    include_package_data=True,
    platforms='any',
    license='MIT',
    description="Websocket protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=version,
    entry_points={
        'console_scripts': [
            'adsocket=adsocket.server:run_loop'
        ]
    },
    classifiers=[
      "Programming Language :: Python :: 3.7",
      "Programming Language :: Python :: 3.8",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
      "Development Status :: 4 - Beta"
    ],
)
