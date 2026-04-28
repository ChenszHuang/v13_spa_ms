from odoo import models, fields, api

THERAPIST_TYPE_LABEL = {
    'full_time': 'Full Time',
    'freelance': 'Freelance',
}

class TherapistActivityAbstract(models.AbstractModel):
    _name = "report.v13_spa_ms.therapist_activity_report"
    _description = "Therapist Activity Report Abstract"


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['print.therapist.activity.report'].browse(docids)
        date_from = docs.date_from
        date_to = docs.date_to
        result = self._get_report_data(date_from, date_to)
        items = self.mapping_report(result)

        if not items:
            raise models.UserError("No data found for this report.")
        
        return {
            'doc_ids': docids,
            'doc_model': 'print.therapist.activity.report',
            'docs': docs,
            'date_from': date_from,
            'date_to': date_to,
            'items':items,
            'company_id':self.env.company,
        }
    
    def mapping_report(self, result):
        therapists = {}

        for row in result:
            tid = row['therapist_id']

            if tid not in therapists:
                therapists[tid] = {
                    'therapist_name': row['therapist_name'],
                    'therapist_type': THERAPIST_TYPE_LABEL.get(row['therapist_type'], row['therapist_type'] or ''),
                    'total_qty': 0,
                    'total_hours': 0.0,
                    'dates': {},
                }

            t = therapists[tid]
            sdate = row['session_date']

            if sdate not in t['dates']:
                t['dates'][sdate] = {
                    'session_date': sdate,
                    'total_qty': 0,
                    'total_hours': 0.0,
                    'products': [],
                }

            d = t['dates'][sdate]
            d['products'].append({
                'product_name': row['product_name'],
                'duration': row['duration'],
                'qty': row['qty'],
                'total_hours': float(row['total_hours']),
            })

            d['total_qty']   += row['qty']
            d['total_hours'] += float(row['total_hours'])

            t['total_qty']   += row['qty']
            t['total_hours'] += float(row['total_hours'])

        result_list = []
        for tdata in therapists.values():
            tdata['dates'] = sorted(
                tdata['dates'].values(),
                key=lambda x: x['session_date']
            )
            result_list.append(tdata)

        result_list.sort(key=lambda x: x['therapist_name'])

        for tdata in result_list:
            tdata['_row_count'] = sum(
                len(d['products']) for d in tdata['dates']
            )

        return result_list
    
    
    def _get_report_data(self, date_from, date_to):
        query = """
            SELECT
                ss.therapist_id,
                COALESCE(rp.therapist_code, '') || ' ' || rp.name AS therapist_name,
                rp.therapist_type,
                DATE(ss.start_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Jakarta') AS session_date,
                pt.id AS product_id,
                pt.name AS product_name,
                pt.duration AS duration,
                COUNT(ss.id) AS qty,
                ROUND(SUM(EXTRACT(EPOCH FROM (ss.end_time - ss.start_time)) / 3600.0)::numeric, 2) AS total_hours
            FROM spa_session ss
                INNER JOIN res_partner rp ON rp.id = ss.therapist_id
                INNER JOIN product_product pp ON pp.id = ss.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                INNER JOIN spa_order so ON so.id = ss.spa_order_id
            WHERE
                DATE(ss.start_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Jakarta') >= %(date_from)s
                AND DATE(ss.start_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Jakarta') <= %(date_to)s
                AND so.state = 'done'
                AND ss.state = 'done'
            GROUP BY
                ss.therapist_id,
                rp.therapist_code,
                rp.name,
                rp.therapist_type,
                DATE(ss.start_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Jakarta'),
                pt.id,
                pt.name,
                pt.duration
            ORDER BY
                rp.name,
                session_date,
                pt.name,
                pt.duration
        """
        self.env.cr.execute(query, {
            'date_from': date_from,
            'date_to': date_to,
        })
        return self.env.cr.dictfetchall()