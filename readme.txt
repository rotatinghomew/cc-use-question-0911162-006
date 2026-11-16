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

版本间影响分析（fixtures/impact_acceptance.json）：
运行迁移时若 fixture 提供 mapping_set / source_version / target_version，系统会先做
跨版本影响分析，再让迁移闸门参与每条记录的迁移决定。
- 输出 impact-analysis.json：受影响下游概念、仍可比较与不可比较的使用率统计、原因码。
- 输出 mapping-chains.csv：逐条可追溯的映射链（hop、relation、status、confidence）。
- 原因码区分 migration（纯迁移、数值不变）、data_change（链可比但实际数据变化）、
  no_equivalent（尚无等价项，保留不可比状态，绝不静默沿用旧值）、mapping_gap
  （映射覆盖不足）、unadopted_link（等价映射尚未采纳）、snapshot_missing、chain_cycle。
- 闸门为 hold 时所有迁移决定一并 hold，并在决策 reasons 中记录 impact_block 原因。

运行影响分析验收：
python3 -m governance_vocabulary run --fixture fixtures/impact_acceptance.json --database /tmp/impact.sqlite3 --output /tmp/impact-output

按当时映射版本核验已采纳的历史报告（含映射指纹与逐条映射边重算）：
python3 -m governance_vocabulary verify-report --database /tmp/impact.sqlite3 --analysis-id <analysis_id>

影响分析模块测试：
python3 -m unittest tests.impact.test_impact_analysis -v
