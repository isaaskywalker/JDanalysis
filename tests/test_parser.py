import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'.agents/skills/job-posting-analysis/scripts/parser.py'
s=importlib.util.spec_from_file_location('parser',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class ParserTests(unittest.TestCase):
    def test_saramin_identity_is_preserved(self):
        r=m.normalize('https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=123&view_type=search&utm_source=x')
        self.assertEqual(r['posting_id'],'123')
        self.assertIn('rec_idx=123',r['canonical_url'])
        self.assertIn('view_type=search',r['canonical_url'])
        self.assertNotIn('utm_source',r['canonical_url'])
    def test_jobkorea_id(self):
        self.assertEqual(m.normalize('https://www.jobkorea.co.kr/Recruit/GI_Read/50081355?Oem_Code=C1')['posting_id'],'50081355')
    def test_generic_functional_query(self):
        self.assertIn('id=123&lang=en',m.normalize('https://careers.example.com/job?id=123&lang=en')['canonical_url'])
    def test_keywords_do_not_prove_completeness(self):
        self.assertEqual(m.assess('담당업무 지원자격 우대사항 경력')['status'],'PARTIAL')
    def test_credentials_and_local_schemes(self):
        for url in ['file:///etc/passwd','https://u:p@example.com']:
            with self.assertRaises(ValueError): m.normalize(url)
if __name__=='__main__': unittest.main()
