import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from src.ipoker import parse_ipoker_xml, money
from src.stats import observations
from src.db import connect, insert_hands, set_label, filtered_observations
from src.mathutils import wilson

XML = (Path(__file__).resolve().parent.parent/'samples'/'ejemplo_ficticio.xml').read_bytes()

class ParserTests(unittest.TestCase):
    def test_money(self):
        self.assertEqual(money('1,679.00'), 1679.00)
        self.assertEqual(money('1.679,00'), 1679.00)
        self.assertEqual(money('€0,10'), 0.1)
    def test_hands_and_facts(self):
        hands, warnings = parse_ipoker_xml(XML, 'example.xml','5s')
        self.assertEqual(len(hands),3)
        self.assertEqual(warnings,[])
        o = [x for h in hands for x in observations(h)]
        self.assertEqual(len(o),7)
        self.assertEqual([(x.spot,x.result) for x in o[:2]], [('SB_FIRST','raise'),('BB_VS_SB_RAISE','fold')])
        self.assertEqual([(x.spot,x.result) for x in o[2:4]], [('SB_FIRST','limp'),('BB_VS_SB_LIMP','check')])
        self.assertEqual([(x.spot,x.result) for x in o[4:]], [('BTN_FIRST','fold'),('SB_FIRST','raise'),('BB_VS_SB_RAISE','call')])
    def test_reject_dtd(self):
        with self.assertRaisesRegex(ValueError,'DTD'):
            parse_ipoker_xml(b'<!DOCTYPE foo><session></session>','x','5s')
    def test_db_and_labels(self):
        hands, _ = parse_ipoker_xml(XML,'e','5s')
        fact = [x for h in hands for x in observations(h)]
        with TemporaryDirectory() as td:
            conn = connect(Path(td)/'a.sqlite')
            self.assertEqual(insert_hands(conn,hands,fact),(3,7))
            self.assertEqual(insert_hands(conn,hands,fact),(0,0))
            set_label(conn,'EJEMPLO_REG','Reg')
            rows = filtered_observations(conn,'SB_FIRST','Todos','Todos',0,50,'Reg')
            self.assertEqual(len(rows),1)
            conn.close()
    def test_wilson(self):
        lo,hi = wilson(50,100)
        self.assertLess(lo,0.5)
        self.assertGreater(hi,0.5)

if __name__=='__main__': unittest.main()
