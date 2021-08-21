import pathlib
from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding='utf-8')

requirements = [
    'requests',
    'PySocks'
]

setup(
    name='PyPasser',
    version='0.0.1',
    author='xHossein',
    url='https://github.com/xHossein/PyPasser',
    install_requires=requirements,
    keywords='Bypass reCaptchaV3',
    description='Bypass reCaptcha V3 only by sending requests.',
    long_description=README,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    python_requires=">=3.7",
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)