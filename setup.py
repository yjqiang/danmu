import re
import pathlib

from setuptools import setup


HERE = pathlib.Path(__file__).parent

txt = (HERE / 'danmu_abc' / '__init__.py').read_text('utf-8')
try:
    version = re.findall(r"^__version__ = '([^']+)'\r?$", txt, re.M)[0]
except IndexError:
    raise RuntimeError('Unable to determine the version.')


def read(f):
    return (HERE / f).read_text('utf-8').strip()


setup(
    name='danmu_abc',
    packages=['danmu_abc'],
    version=version,
    description='Danmu for humans.',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    license='MIT',
    author='yjqang',
    author_email='yjqiang01@gmail.com',
    url='https://github.com/yjqiang/danmu',
    keywords=[
        'danmu', 'huya', 'bilibili', 'douyu'
    ],
    install_requires=[
        'aiohttp>=3.6.2,<4.0.0',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
)
