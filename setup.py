from setuptools import setup, find_packages

version = '1.0'

setup(
    name='tn.plonehtmlimagecache',
    version=version,
    description='',
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
    ],
    keywords='',
    author='TN Tecnologia e Negocios',
    author_email='ed@tecnologiaenegocios.com.br',
    url='http://www.tecnologiaenegocios.com.br',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['tn'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'five.grok',
        'Plone',
        'plone.directives.form',
        'plone.behavior',
        'plone.app.intid',
        'plone.namedfile[blobs]',
        'lxml',
    ],
    extras_require={
        'test': [
            'stubydoo',
            'zope.app.testing',
        ]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
