from odoo import models, fields, api

class PayoutCommissionReportAbstract(models.AbstractModel):
    _name = "report.v13_spa_ms.payout_commission_report"
    _description = "Payout Commission Report Abstract"


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['print.payout.commission.report'].browse(docids)
        date_from = docs.date_from
        date_to = docs.date_to
        result = self._get_report_data(date_from, date_to)
        items = self.mapping_report(result)

        if not items:
            raise models.UserError("No data found for this report.")
        
        grand_total = {
        'qty': sum(g['total_qty'] for g in items),
    }
        
        return {
            'doc_ids': docids,
            'doc_model': 'print.revenue.report',
            'docs': docs,
            'date_from': date_from,
            'date_to': date_to,
            'items':items,
            'grand_total':grand_total,
            'company_id':self.env.company,
        }
    
    
    def mapping_report(self, result):
        customers = {}

        for row in result:
            cid = row['customer_id']

            if cid not in customers:
                customers[cid] = {
                    'customer_name': row['customer_name'],
                    'total_qty': 0,
                    'total_commission': 0.0,
                    'guides': {},
                }

            c = customers[cid]
            gid = row['guide_id']

            if gid not in c['guides']:
                c['guides'][gid] = {
                    'guide_name': row['guide_name'],
                    'total_qty': 0,
                    'total_commission': 0.0,
                    'orders': {},
                }

            g = c['guides'][gid]
            oname = row['order_name']

            if oname not in g['orders']:
                g['orders'][oname] = {
                    'order_name': oname,
                    'order_date': row['order_date'],
                    'ref': row['order_ref'],
                    'total_qty': 0,
                    'total_commission': 0.0,
                    'treatments': [],
                    '_row_count': 0,
                }

            o = g['orders'][oname]

            o['treatments'].append({
                'product_name': row['product_name'],
                'qty': row['qty'],
                'commission_amount': row['commission_amount'],
                'total_commission': row['total_commission'],
            })

            o['_row_count']       += 1
            o['total_qty']        += row['qty']
            o['total_commission'] += row['total_commission']

            g['total_qty']        += row['qty']
            g['total_commission'] += row['total_commission']

            c['total_qty']        += row['qty']
            c['total_commission'] += row['total_commission']

        # convert ke list
        result_list = []
        for cdata in customers.values():
            for gdata in cdata['guides'].values():
                gdata['orders'] = sorted(
                    gdata['orders'].values(),
                    key=lambda x: x['order_date']
                )
            cdata['guides'] = sorted(
                cdata['guides'].values(),
                key=lambda x: x['guide_name']
            )
            result_list.append(cdata)

        result_list.sort(key=lambda x: x['customer_name'])
        return result_list
    
    
    def _get_report_data(self, date_from, date_to):
        query = """
            SELECT
                so.partner_id AS customer_id,
                COALESCE(rc.ref, '') || ' ' || rc.name AS customer_name,
                so.guide_id,
                COALESCE(rg.ref, '') || ' ' || rg.name AS guide_name,
                so.number AS order_name,
                so.reference AS order_ref,
                so.date AS order_date,
                pt.name AS product_name,
                ss.commission_amount,
                COUNT(ss.id) AS qty,
                COALESCE(ss.commission_amount, 0) AS commission_amount,
                COALESCE(SUM(ss.commission_amount), 0) AS total_commission
            FROM spa_session ss
                INNER JOIN spa_order so ON so.id = ss.spa_order_id
                INNER JOIN res_partner rc ON rc.id = so.partner_id
                INNER JOIN res_partner rg ON rg.id = so.guide_id
                INNER JOIN product_product pp ON pp.id = ss.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE
                so.date >= %(date_from)s
                AND so.date <= %(date_to)s
                AND so.state = 'done'
                AND (
                    rc.is_travel_agent = TRUE
                    OR rc.is_guide = TRUE
                )
            GROUP BY
                so.partner_id, rc.ref, rc.name,
                so.guide_id, rg.ref, rg.name,
                so.id, so.number, so.date,
                pt.id, pt.name,
                ss.commission_amount, so.reference
            HAVING 
                COALESCE(SUM(ss.commission_amount), 0) > 0
            ORDER BY
                rc.name, rg.name, so.date, so.number, pt.name
        """
        self.env.cr.execute(query, {'date_from': date_from, 'date_to': date_to})
        return self.env.cr.dictfetchall()