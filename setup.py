from setuptools import setup, find_packages

setup(
    name = 'dataframe-browser',
    version = "0.2.0.dev0",
    description = """Interactive pandas dataframe browser""",
    author = "Nicholas Cain",
    author_email = "nicain.seattle@gmail.com",
    url = 'https://github.com/nicain/dataframe-browser',
    packages = find_packages(),
    include_package_data=True,
    setup_requires=['pytest-runner'],
    install_requires=['pandas', 'networkx', 'argcomplete'],
    scripts=['bin/dataframe-browser']
)
