from setuptools import setup

setup(name='mp_driver',
      version='0.1',
      description='A webdriver extension for MPathways',
      author='Jamie Davis',
      author_email='jamjam@umich.edu',
      license='MIT',
      packages=['mp_driver'],
      install_requires=[
        'selenium'
      ],
      zip_safe=False)