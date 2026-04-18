from odoo import models, fields, api

class RevenueReportAbstract(models.AbstractModel):
    _name = "report.v13_spa_ms.revenue_report"
    _description = "Revenue Report Abstract"


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['print.revenue.report'].browse(docids)
        date_from = docs.date_from
        date_to = docs.date_to
        result = self._get_report_data(date_from, date_to)
        items = self.mapping_revenue_report(result)

        if not items:
            raise models.UserError("No data found for this report.")
        
        grand_total = {
        'qty': sum(g['total_qty'] for g in items),
        'gross': sum(g['total_gross'] for g in items),
        'discount': sum(g['total_discount'] for g in items),
        'net': sum(g['total_net'] for g in items),
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


    def mapping_revenue_report(self, result):
        groups = {}

        for row in result:
            type_id = row['type_id']

            if type_id not in groups:
                groups[type_id] = {
                    'type_code': row['type_code'],
                    'type_name': row['type_name'],
                    'total_qty': 0,
                    'total_gross': 0.0,
                    'total_discount': 0.0,
                    'total_net': 0.0,
                    'treatments': [],
                }

            groups[type_id]['treatments'].append({
                'code': row['code'],
                'name': row['product_name'],
                'qty': row['qty'],
                'gross': row['gross'],
                'discount_pct': row['discount_pct'],
                'discount_amount': row['discount_amount'],
                'net': row['net'],
            })

            groups[type_id]['total_qty']      += row['qty']
            groups[type_id]['total_gross']    += row['gross']
            groups[type_id]['total_discount'] += row['discount_amount']
            groups[type_id]['total_net']      += row['net']

        return list(groups.values())


    def _get_report_data(self, date_from, date_to):
        query = """
            SELECT
                tt.id AS type_id,
                tt.code as type_code,
                tt.name AS type_name,
                pt.id AS product_id,
                pt.treatment_code as code,
                pt.name AS product_name,
            COUNT(ss.id) AS qty,
            SUM(aml.price_unit) AS gross,
            AVG(ss.discount) AS discount_pct,
            SUM(
                (aml.price_unit* aml.quantity) * (ss.discount / 100.0)
            ) AS discount_amount,
            SUM(
               (aml.price_unit * aml.quantity) - ((aml.price_unit * aml.quantity) * (ss.discount / 100.0))
            ) AS net
            FROM
                spa_session ss
                INNER JOIN spa_order so
                    ON so.id = ss.spa_order_id
                INNER JOIN account_move_line aml
                    ON aml.spa_session_id = ss.id
                INNER JOIN account_move am
                    ON am.id = aml.move_id
                INNER JOIN product_product pp
                    ON pp.id = ss.product_id
                INNER JOIN product_template pt
                    ON pt.id = pp.product_tmpl_id
                INNER JOIN treatment_type tt
                    ON tt.id = pt.treatment_type_id
            WHERE
                so.date >= %(date_from)s
                AND so.date <= %(date_to)s
                AND so.state = 'done'
                AND am.state = 'posted'
                AND am.type IN ('out_invoice', 'out_receipt')
            GROUP BY
                tt.id, tt.code, tt.name,
                pt.id, pt.treatment_code, pt.name
            ORDER BY
                tt.id, pt.name
        """
        self.env.cr.execute(query, {
            'date_from': date_from,
            'date_to': date_to,
        })
        return self.env.cr.dictfetchall()
       

    



        