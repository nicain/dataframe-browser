from setuptools import setup, find_packages

setup(
    name = 'dataframe-browser',
    version = '0.1.0',
    description = """Interactive pandas dataframe browser""",
    author = "Nicholas Cain",
    author_email = "nicain.seattle@gmail.com",
    url = 'https://github.com/nicain/dataframe-browser',
    packages = find_packages(),
    include_package_data=True,
    setup_requires=['pytest-runner'],
    install_requires=['pandas', 'networkx', 'argcomplete'],
    entry_points={
          'console_scripts': [
              'dataframe-browser = dataframe_browser.__main__:main'
        ]
    },
)
