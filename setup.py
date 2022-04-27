import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='suffersync',
    version='1.4.2',
    description='Syncs workouts from Wahoo SYSTM to intervals.icu',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/bakermat/suffersync',
    author='Bakermat',
    author_email='',
    license='MIT',
    py_modules=['suffersync'],
    install_requires=[
        'requests>=2.26'
    ],
    entry_points={
        'console_scripts': [
            'suffersync=suffersync:main',
        ],
    },
)
