多国人工智能治理术语本体版本迁移库

运行验收：
python3 -m governance_vocabulary run --fixture fixtures/acceptance.json --database /tmp/governance_vocabulary.sqlite3 --output /tmp/governance_vocabulary-output

核验：
python3 -m governance_vocabulary verify --database /tmp/governance_vocabulary.sqlite3 --output /tmp/governance_vocabulary-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.semantic_signal.test_semantic_stability -v

构建检查：
python3 -m compileall -q governance_vocabulary tests
