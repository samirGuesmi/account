# -*- coding: utf-8 -*-
##############################################################################
#
#
#   Samir GUESMI :
#   samir.guesmi86@gmail.com
#
##############################################################################


{
    'name': "Account Payment Importation",
    'category' : "Account/Payment",
    'version': '1.0',
    'author' : 'Samir GUESMI',
    'description': """
Import Supplier Payment Via CSV Files
==========================================
    """,
    'data': [
        #Security
        'security/ir.model.access.csv',

        #Views
        'views/order_payment_view.xml',


    ],
    'depends': [
        'account_payment',
        'purchase',
        'sale',
    ],

    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
