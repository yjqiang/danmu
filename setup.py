from setuptools import setup

VERSION = '0.1.0'


setup(
    name='danmu_abc',
    packages=['danmu_abc'],
    version=VERSION,
    description='Danmu for humans.',
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
