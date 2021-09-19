import pathlib
from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding='utf-8')

requirements = [
    'requests==2.25.1',
    'PySocks==1.7.1',
]

setup(
    name='PyPasser',
    version='0.0.4',
    author='xHossein',
    license='MIT',
    url='https://github.com/xHossein/PyPasser',
    install_requires=requirements,
    keywords=[
        'Bypass reCaptcha V3','Bypass-reCaptcha-V3','Bypass reCaptcha',
        'Bypass-reCaptcha','Google reCaptcha','Google-reCaptcha'
    ],
    description='Bypass reCaptcha V3 only by sending HTTP requests.',
    long_description=README,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    python_requires=">=3.7",
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)