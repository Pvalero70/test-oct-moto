# -*- coding: utf-8 -*-
{
    'name': 'Neuprosa theme',
    'description': 'Sitio Web Neuprosa',
    'version': '1.0',
    'author': '@glopzvega',
    'category': 'Theme/Creative',
    'depends': ['website'],
    'data': [
        # 'views/layout.xml',
        'views/snippets.xml',
        'views/home.xml',
        'views/services.xml',
        'views/header.xml',
        'views/footer.xml',
    ],
    'assets' : {    
        'web.assets_frontend': [
            "/theme_neuprosa/static/fonts/stylesheet.css",
            "/theme_neuprosa/static/fonts/stylesheet2.css",
            "/theme_neuprosa/static/scss/style.scss",
            "/theme_neuprosa/static/scss/style_mobile.scss",
            "/theme_neuprosa/static/scss/homepage.scss",
            "/theme_neuprosa/static/scss/homepage_mobile.scss",
            "/theme_neuprosa/static/scss/services.scss",
        ],
        'web._assets_primary_variables': [
            "/theme_neuprosa/static/scss/primary_variables.scss",
        ],
        'web._assets_frontend_helpers': [
            "/theme_neuprosa/static/scss/bootstrap_overridden.scss",
        ]
    },
    'application': False,
    'installable': True,
    'price': 0.00,
    'currency': 'USD',
    'license': 'OPL-1',
}