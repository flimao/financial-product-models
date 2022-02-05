from setuptools import setup

setup(
    name = 'finance_models',
    version = '0.1.0',    

    description = 'Models for predicting prices of several financial products',
    url = 'https://github.com/flimao/financial-product-models',
    author = 'Felipe Oliveira',
    author_email = 'financemodels@dev.lmnice.me',
    license = 'GNU GPLv3',
    packages = ['finance_models'],
    install_requires = [
        'numpy', 'pandas',
    ],

    classifiers = [
        'Development Status :: 1 - Planning',
        'Intended Audience :: Finance',
        'License :: OSI Approved :: GNU GPLv3',         
        'Programming Language :: Python :: 3',
    ],
)
