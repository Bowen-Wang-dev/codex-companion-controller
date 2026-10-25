# Synthetic billing fixtures; no actual account export is distributed.
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bridge'))
from provider_billing import parse_export,reconcile,supplements
from usage_meter import UsageLedger,plus
from test_usage_ledger import BOOK,MODEL,tokens


class ProviderBillingTests(unittest.TestCase):
    header='Time\tAPI Key Name\tModel\tInput Tokens\tOutput Tokens\tCache Read Tokens\tCache Creation Tokens\tRate Multiplier\tBilled Cost\n'
    def row(self,time='2026-01-01T10:00:00+08:00',i=5000,o=100,c=0,cost='0.00198000'):
        return '\t'.join(map(str,(time,'private-key-name',MODEL,i,o,c,0,.5,cost)))+'\n'

    def test_uncached_export_input_and_discounted_cost_are_not_counted_twice(self):
        rows=parse_export(self.header+self.row(i=1000,o=200,c=4000,cost='0.00079200'))
        self.assertEqual(rows[0]['usage']['inputTokens'],5000)
        report=reconcile(rows,[],BOOK)
        self.assertEqual(report['provider_billed_cost'],'0.00079200')
        self.assertAlmostEqual(report['local_rate_estimate'],.000792)
        self.assertNotIn('private-key-name',json.dumps(rows))

    def test_unique_counter_model_and_timestamp_match(self):
        rows=parse_export(self.header+self.row())
        local=[dict(rows[0],at=rows[0]['at']+.2)]
        self.assertEqual(reconcile(rows,local,BOOK)['matched_rows'],1)
        local[0]['usage']=tokens()
        report=reconcile(rows,local,BOOK)
        self.assertEqual(report['matched_rows'],0)
        self.assertEqual(report['missing_local'][0]['usage']['totalTokens'],5100)

    def test_invalid_rows_and_ambiguous_duplicates_fail_explicitly(self):
        for body in (self.header+self.row(i=-1),self.header+self.row(cost='NaN'),
                     self.header+self.row()+self.row()):
            with self.assertRaises(ValueError):parse_export(body)

    def test_csv_export_and_timezone(self):
        text=(self.header+self.row()).replace('\t',',')
        row=parse_export(text)[0]
        import datetime
        self.assertEqual(datetime.datetime.fromtimestamp(row['at'],datetime.timezone.utc).hour,2)

    def test_supplement_requires_unique_enclosing_turn_and_late_local_removes_it(self):
        row=parse_export(self.header+self.row())[0]
        local=[{'thread':'thread','turn':'turn','at':row['at']-10,'model':MODEL,'usage':tokens()},
               {'thread':'thread','turn':'turn','at':row['at']+10,'model':MODEL,'usage':tokens()}]
        added=supplements([row],local)
        self.assertEqual(len(added),1);self.assertEqual(added[0]['turn'],'turn')
        m=UsageLedger();m.reset_at=0;m.observe_responses([dict(r,id=str(i)*64) for i,r in enumerate(local)])
        m.reconcile_provider(added)
        before=m.view('thread','turn',MODEL,BOOK)['usage']['total']
        self.assertEqual(before['totalTokens'],2600+5100)
        late=dict(row,thread='thread',turn='turn')
        m.observe_responses([late]);m.reconcile_provider(supplements([row],local+[late]))
        self.assertEqual(m.view('thread','turn',MODEL,BOOK)['usage']['total'],before)
        self.assertFalse(m.provider_turns)

    def test_export_outside_known_turn_is_not_assigned_to_active_chat(self):
        row=parse_export(self.header+self.row())[0]
        local=[{'thread':'thread','turn':'turn','at':row['at']-10,'model':MODEL,'usage':tokens()}]
        self.assertEqual(supplements([row],local),[])


if __name__=='__main__':unittest.main()
