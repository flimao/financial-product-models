from setuptools import setup

setup(
    name = 'finance_models',
    version = '1.4.0',    

    description = 'Models for predicting prices of several financial products',
    url = 'https://github.com/flimao/financial-product-models',
    author = 'Felipe Oliveira',
    author_email = 'financemodels@dev.lmnice.me',
    long_description = open('README.md').read(),
    license = 'LICENSE',
    packages = ['finance_models', 'finance_models.test', 'finance.models.derivatives'],
    install_requires = [
        'numpy', 'scipy', 'pandas', 'babel'
    ],

    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',        
        'Programming Language :: Python :: 3 :: Only',
    ],
)
