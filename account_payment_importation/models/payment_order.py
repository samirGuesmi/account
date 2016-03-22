# -*- coding: utf-8 -*-
##############################################################################
#
#
#   Samir GUESMI :
#   samir.guesmi86@gmail.com
#
##############################################################################


from openerp.osv import fields, osv
from openerp.tools.translate import _
import base64
import re

# def convertXLS2CSV(aFile):
#     '''converts a MS Excel file to csv w/ the same name in the same directory'''
#
#     print "------ beginning to convert XLS to CSV ------"
#
#     try:
#         import win32com.client, os
#         from win32com.client import constants as c
#         excel = win32com.client.Dispatch('Excel.Application')
#
#         fileDir, fileName = os.path.split(aFile)
#         nameOnly = os.path.splitext(fileName)
#         newName = nameOnly[0] + ".csv"
#         outCSV = os.path.join(fileDir, newName)
#         workbook = excel.Workbooks.Open(aFile)
#         workbook.SaveAs(outCSV, c.xlCSVMSDOS) # 24 represents xlCSVMSDOS
#         workbook.Close(False)
#         excel.Quit()
#         del excel
#
#         print "...Converted " + nameOnly + " to CSV"
#     except:
#         print ">>>>>>> FAILED to convert " + aFile + " to CSV!"

class payment_order(osv.osv):
    _inherit = 'payment.order'

    _columns = {
        'import_file' : fields.binary('Import Payment'),
        'error_ids': fields.one2many('payment.order.importation.error', 'order_id', 'Not Imported Lines', readonly=True),
    }


    def _chech_line(self, cr, uid, csv_line):
        '''
            Return True if condition is correct
        '''
        if len(csv_line) == 7 :
            return True
        return False

    #Update line_ids list and importation.error list
    def onchange_imported_file(self, cr, uid, ids, import_file, reference, date_prefered, mode, user_id):
        if not import_file :
            return {}
        if not mode :
            raise osv.except_osv(_('Error!'), _('Please Define a Payment Mode first.'))

        recordlist = unicode(base64.decodestring(import_file), 'windows-1252', 'strict').split('\n')
        line_ids = []
        not_imported_lines = []
        if not ids :
            #Create payment_order
            order_id = self.create(cr, uid, {'reference' : reference, 'date_prefered': date_prefered, 'mode' : mode, 'user_id' : user_id})
        else :
            order_id = ids[0]
        PATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
        po_pool = self.pool.get('purchase.order')
        so_pool = self.pool.get('sale.order')
        invoice_pool = self.pool.get('account.invoice')
        account_move_pool = self.pool.get('account.move.line')
        for line in recordlist:
            print line
            element = PATTERN.split(line)[1::2]
            #TEST if the line is good
            if self._chech_line(cr, uid, element) :
                customer_invoice = element[4].replace(' ', '') #Delete whitespace
                invoice_id = invoice_pool.search(cr, uid, [('number', '=', customer_invoice.replace('"', ''))])
                if invoice_id :
                    invoice = invoice_pool.browse(cr, uid, invoice_id)
                    so = so_pool.search(cr, uid, [('invoice_ids', '=', [invoice.id])])
                    if so :
                        po = po_pool.search(cr, uid, [('sale_id', '=', so[0])])
                        if po :
                            for supplier_invoice in po_pool.browse(cr, uid, po).invoice_ids :
                                move_line_id = account_move_pool.search(cr, uid,
                                                                        [('reconcile_id', '=', False),
                                                                        ('credit', '>', 0),
                                                                        ('account_id.reconcile', '=', True),
                                                                        ('invoice', '=', supplier_invoice.id)
                                                                         ])
                                if move_line_id :
                                    move_line = account_move_pool.browse(cr, uid, move_line_id[0])
                                    line_ids.append(self._add_payment_order_line(cr, uid, order_id, move_line))
                                #move line not found
                                else :
                                    not_imported_lines.append(self._add_not_imported_lines(cr, uid, order_id, customer_invoice, _('Move line not found')))
                        #in case of purchase order not found
                        else :
                            not_imported_lines.append(self._add_not_imported_lines(cr, uid, order_id, customer_invoice, _('Purchase Order not found')))
                    #sale order not found
                    else :
                        not_imported_lines.append(self._add_not_imported_lines(cr, uid, order_id, customer_invoice, _('Sale Order not found')))
                else: #Invoice not found
                    not_imported_lines.append(self._add_not_imported_lines(cr, uid, order_id, customer_invoice, _('Invoice Not found')))

        return {'value' : {'line_ids' : line_ids, 'error_ids' : not_imported_lines}}

    def _add_payment_order_line(self, cr, uid, id, move_line):
        '''
        :param move_line: Move_line obj
        :return: Id of payment line created
        '''
        parent = self.pool.get('payment.order').browse(cr, uid, id)
        payment_line = self.pool.get('payment.line')
        vals = {'order_id' : id, 'move_line_id' : move_line.id}
        curency = move_line.invoice.currency_id.id
        company_currency = move_line.invoice.company_id.currency_id.id
        vals.update(payment_line.onchange_move_line(cr, uid, [move_line.id], move_line.id, parent.mode.id, parent.date_prefered, parent.date_scheduled, curency, company_currency)['value'])
        return payment_line.create(cr, uid, vals)

    def _add_not_imported_lines(self, cr, uid, id, ref, reason):
        '''
        :param ref:  Invoice Ref
        :param reason:  Error msg
        '''
        return self.pool.get('payment.order.importation.error').create(cr, uid, {'order_id' : id, 'name' : ref, 'reason' : reason})


payment_order()


class importation_error_line(osv.Model):
    _name = 'payment.order.importation.error'

    _columns = {
        'order_id': fields.many2one('payment.order', 'Order', required=True,
            ondelete='cascade', select=True),
        'name' : fields.char('Ref'),
        'reason' : fields.char('Reason'),
    }

importation_error_line()

#for testing Only #TODO : to delete the following lines
class po(osv.Model):
    _inherit = 'purchase.order'

    _columns = {
        'sale_id' : fields.many2one('sale.order', 'Sale Order')
    }

po()
