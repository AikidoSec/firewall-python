{
    'name': 'sample app aikido-zen',
    'version': '0.0.1',
    'category': 'Tools',
    'summary': 'Sample application for testing Aikido security',
    'description': 'This is used for testing Aikido Zen',
    'author': 'Aikido Security',
    'website': 'https://aikido.dev',
    'license': 'AGPL',
    'depends': ['base', 'web'],
    'external_dependencies': {
        'python': ['MySQLdb', 'aikido_zen', 'sentry_sdk', 'requests'],
    },
    'data': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
