# 长期记忆

## 工作空间路径变更（2026-02-24）
**重要更新**：工作空间路径已从 `/Users/blastai/.openclaw/workspace-0011ai` 变更为 `/Users/blastai/.openclaw/workspace-oai`

所有后续操作、文件读写、任务执行都将基于新路径进行。

## 🔑 API Keys 配置

### Brave Search API Keys（更新于 2026-02-20）
**配置位置**: `~/.zshrc`

| 环境变量 | 用途 | Key | 状态 |
|---------|------|-----|------|
| `BRAVE_API_KEY` | 搜索 API | `BSAZ6SYvR2UtXQegygALCsfpJsBw8tY` | ✅ 有效 |
| `BRAVE_ANSWERS_API_KEY` | Answers API | `BSAIbAcNjVQEVvpcMjM35QBeXQg64xY` | ✅ 有效 |
| `BRAVE_AUTOSUGGEST_API_KEY` | Autosuggest API | `BSAEtJNAkwud-1LmRDsE-VBuwA1sytp` | ✅ 有效 |
| `BRAVE_SPELLCHECK_API_KEY` | Spellcheck API | `BSASrEXdvIOcowi8l1PHqNILRRMwGvT` | ✅ 有效 |

### Tavily Search API（更新于 2026-02-25）
**配置位置**: `~/.zshrc`

| 环境变量 | 用途 | Key | 状态 |
|---------|------|-----|------|
| `TAVILY_API_KEY` | 搜索 API | `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` | ✅ 有效 |

**用途**:
- 实时网络搜索
- 支持中文搜索
- 返回结构化结果 + AI 生成的答案
- 比 Brave Search 更适合实时数据查询

**API 端点**: `https://api.tavily.com/search`

**对比**:
| 特性 | Tavily | Brave Search |
|------|--------|--------------|
| 中文支持 | ✅ 优秀 | ⚠️ 一般 |
| 实时性 | ✅ 快速 | ✅ 快速 |
| AI 答案 | ✅ 内置 | ❌ 需要额外调用 |

**建议**：Tavily 更适合 A 股相关的实时搜索任务。

### iTick API Key（更新于 2026-02-25）
**配置位置**: `~/.zshrc`

| 环境变量 | 用途 | Key | 状态 |
|---------|------|-----|------|
| `ITICK_API_KEY` | 美股/港股实时行情 | `ec8cdf339fe945ca823725b74ad8ec49b19ec164b16e4c9f924ad4674496c355` | ✅ 有效 |

**注意**：iTick 不支持 A 股，仅支持美股和港股
**免费额度**：200 次/日
**用途**：美股实时行情（优先于 yfinance）

### TuShare Pro Token（更新于 2026-02-25）
**配置位置**: `~/.zshrc`

| 环境变量 | 用途 | Token | 状态 |
|---------|------|-------|------|
| `TUSHARE_TOKEN` | A股金融数据 | `3421453a76aea411f074906d9ef4ec5ac9d053fc88e5d1327d06a581` | ✅ 有效 |

**可用接口**（测试通过）：
- ✅ `stock_basic` - 股票列表（5484只）
- ❌ `index_daily` - 指数日线（需积分）
- ❌ `trade_cal` - 交易日历（需积分）

**权限说明**：新用户积分有限，高级接口需积分升级
**获取积分**：https://tushare.pro/document/1?doc_id=13

---

## 📈 杰哥策略（量化交易系统）

### 核心指标
- **通达信涨跌家数指数（880005）**：当日市场中上涨股票家数
- **5日移动平均线（MA5）**：中期/整体大盘情绪锚点
- **3日移动平均线（MA3）**：短期/短线投机情绪波动

### 关键阈值（2026-02-26 更新）
| 情绪状态 | 数值范围 | 操作基调 |
|---------|---------|---------|
| **冰点/极值** | **≤ 1300家** | 进攻 |
| **高潮/顶值** | **≥ 4000家** | 防守 |

| 5日线位置 | 数值标准 | 情绪周期 |
|---------|---------|---------|
| 下轨 | MA5 < 2000家 | 冰点/新周期起点 |
| 上轨 | MA5 > 2300-2500家 | 高潮/退潮期初期 |

### 八大情绪周期标签
1. **IcePoint（冰点）**：红盘 ≤ 1300，进攻区域起点
2. **TurnUp（拐点向上）**：MA5确认从下降转为上升
3. **MainRally（主升浪）**：MA5明确上升，黄金做多期
4. **Climax（高潮）**：红盘 ≥ 4000，防守区域
5. **TurnDown（拐点向下）**：MA5确认从上升转为下降
6. **Downtrend（退潮）**：MA5明确下降，亏钱效应扩散
7. **LowShake（低位震荡）**：MA5在下轨横向波动
8. **HighShake（高位震荡）**：MA5在上轨横向波动

### 六大交易模式
| 模式 | 启用周期 | 禁用周期 |
|-----|---------|---------|
| 首板打板（FirstLimit） | TurnUp, MainRality初期, LowShake | Climax, TurnDown |
| 二波反包（SecondWaveWrap） | IcePoint次日, LowShake末期 | HighShake, Climax |
| 拿货分时（AccumulationIntraday） | Climax转TurnDown的指数大跌日 | MainRally, Downtrend |
| 极值套利（ExtremeArbitrage） | IcePoint做多, Climax做空 | 震荡期 |
| 分歧低吸（DipBuy） | MainRally首次强分歧 | Downtrend |
| 一进二（1To2） | TurnUp确认后强化日 | Climax次日, TurnDown初期 |

### 仓位管理
- **凯利公式**：K = (W * R - 1) / (R - 1)
- **进攻区**：单票可重仓，总仓位积极
- **防守区**：单票 ≤ 1-2成，总仓 ≤ 20-30%
- **最大回撤**：控制在 12% 以内

### 买卖点时间窗口
1. **竞价窗口（9:15-9:30）**：情绪定位与先手预判
2. **开盘窗口（9:30-10:30）**：确认与跟随
3. **盘中窗口（10:30-14:30）**：轮动与避险
4. **尾盘窗口（14:30-15:00）**：确认与布局

### 量能阈值
- **容量门槛**：成交额 ≥ 10亿（优选20亿）
- **竞价筛选**：竞价额 > 2000万
- **一进二**：首板成交额 < 8000万（传统标准）
- **撬跌停**：翘板量 ≈ 历史天量日成交的15%-25%

### 风控规则
- **逻辑证伪止损**：买入逻辑被破坏，无论盈亏离场
- **时间止损**：次日午盘仍无溢价，午后离场
- **周期拐点卖出**：CycleTag从MainRally/Climax转为TurnDown
- **模式熔断**：Climax/TurnDown禁用中高位接力，Downtrend禁用波段持有

### 3日线与5日线组合策略
| MA3 | MA5 | 组合标签 | 策略 |
|-----|-----|---------|-----|
| 向上 | 向上 | 主升共振 | 重仓聚焦主线龙头 |
| 向上 | 向下 | 下跌中继/反弹 | 只做套利，绝不格局 |
| 向下 | 向上 | 上升中继/分歧 | 去弱留强，低吸核心 |
| 向下 | 向下 | 双杀退潮 | 空仓或极小仓位 |

**详细文档**：`~/Desktop/jiege/杰哥策略.md`
**原始文档**：`~/Desktop/jiege/杰哥策略_原始文档.docx`
**学习时间**：2026-02-26

---

## 重要资源

- **ClawHub 技能仓库**: https://github.com/VoltAgent/awesome-openclaw-skills
  - 包含 2,999 个社区构建的 OpenClaw 技能
  - 按 28 个类别组织（AI & LLMs, Search & Research, DevOps, Coding 等）
  - 遇到未知任务时，优先在此搜索合适的技能

## 工作准则

- 遇到未知任务 → 先在 ClawHub 搜索相关技能
- 找到合适的技能 → 自动安装并使用
- 技能安装命令: `clawhub install <skill-slug>`
- 技能搜索命令: `clawhub search "关键词"`

## 社交媒体与金融监控技能库

### Twitter/X 监控
- **核心工具**: `bird` CLI
- **认证方式**: Chrome cookies 自动认证
- **功能**: 
  - 获取指定账号最新推文 (`bird read <username>`)
  - 获取转发/引用推文内容
  - 支持多账号监控
- **适用场景**: 投资名人动态、政治人物言论、市场情绪分析

### 微博监控  
- **核心工具**: `news-aggregator-skill`
- **功能**:
  - 获取微博热搜榜 (`--source weibo --limit N`)
  - 关键词搜索 (`--keyword "关键词"`)
  - 深度内容提取 (`--deep` 参数)
- **优化策略**: 需要测试不同关键词格式以获得最佳结果
- **适用场景**: 中文市场动态、热点事件追踪、投资相关话题

### 金融数据监控
- **专业工具**: `MarketPulse` (AIsa API)
- **功能范围**:
  - 股票实时报价和历史数据
  - 加密货币价格监控
  - 财务报表和基本面分析
  - 公司新闻和分析师预期
  - 内幕交易和机构持仓
- **依赖**: 需要 AISA_API_KEY
- **适用场景**: 专业投资分析、组合监控、市场研究

### 股票技术分析
- **工具**: `stock-market-pro` 
- **功能**:
  - 实时股价 (`price` 命令)
  - 专业K线图 (`pro` 命令)
  - 基本面分析 (`fundamentals` 命令)
  - 财报日历 (`earnings` 命令)
- **优势**: 无需API密钥，基于 Yahoo Finance
- **适用场景**: 技术分析、图表生成、基本面快速查看

### 自动化监控策略
- **定时任务**: 使用 cron 设置定期数据获取
- **智能过滤**: 基于热度、关键词、时间窗口筛选重要信息
- **多源验证**: 交叉验证不同平台的信息准确性
- **报告生成**: 自动生成结构化监控报告

### 全球新闻日报来源（更新于 2026-02-19）
**高优先级**：
- TechURLs.com (https://techurls.com) - 科技新闻聚合 ⭐

**RSS 权威媒体**：
- 纽约时报 (NYTimes RSS)
- BBC News (RSS)
- 路透社 (Reuters RSS)

**X 推特高质量账号** (12 个)：
- @Reuters @AP @BBCBreaking @nytimes @Bloomberg @CNN @WSJ @FT @ReutersWorld @BreakingNews @AJEnglish @guardian

**中文新闻源**：
- 华尔街见闻 (财经)
- 微博热搜 (社交)
- 36Kr (科技财经)

## 技能管理

### 核心技能策略
- **已安装技能**：当前 8 个技能标记为核心（永不被清理）
- **新安装技能**：默认不加入核心列表（可被清理）
- **配置文件**: `~/.openclaw/core-skills.json`

### 定期清理规则
- **执行频率**: 每周日凌晨 3:00
- **清理对象**: 仅限未来新安装的技能（超过 10 天未使用）
- **核心技能**: 仅限配置文件中的技能受保护
- **日志位置**: `~/.openclaw/logs/skill-cleanup.log`
- **脚本位置**: `~/.openclaw/scripts/skill-cleanup.sh`

### 紧急清理（防止崩溃）
- **触发条件**: 技能总数 ≥ 50 个
- **清理规则**: 自动删除最旧的 10 个非核心技能
- **预防**: 保持技能库精简

### 管理核心技能
```bash
# 查看核心技能列表
cat ~/.openclaw/core-skills.json

# 添加核心技能（手动）
jq '.core_skills += ["新技能名"]' ~/.openclaw/core-skills.json > /tmp/temp.json && mv /tmp/temp.json ~/.openclaw/core-skills.json
```

### 技能安装检查（重要教训）
**问题**：2026-02-20 发现 `self-reflection` 技能安装后缺少 `bin/` 目录和可执行脚本
**解决方案**：
1. 检查新安装技能是否包含 `bin/` 目录
2. 如果缺失，根据 SKILL.md/README.md 手动创建 CLI 工具
3. 确保脚本可执行：`chmod +x bin/script-name`
4. 更新 cron 任务使用完整路径调用

**检查命令**：
```bash
ls -la ~/.openclaw/workspace/skills/<skill-name>/bin/
```

## 航母位置追踪

### 核心方法
AIS 船舶追踪 + 卫星遥感 + 权威军事情报交叉验证

### 常用航母 MMSI
- USS Theodore Roosevelt (CVN-71): 369078000
- USS George H.W. Bush (CVN-77): 369985000
- USS Ronald Reagan (CVN-76): 369970000
- USS Nimitz (CVN-68): 369924000

### 查询平台
- **AIS**: MarineTraffic, VesselFinder, ShipFinder
- **军事情报**: USNI News (https://news.usni.org)
- **卫星遥感**: Sentinel-1 SAR, Sentinel-2 (https://scihub.copernicus.eu)

### 自动化脚本
- **脚本**: `~/.openclaw/scripts/carrier-tracker.sh`
- **报告**: `~/.openclaw/carrier-tracker/latest_report.md`
- **定时任务**: 每天 8:00 自动追踪

### 重要限制
- 军舰常关闭 AIS 信号
- 卫星有过顶周期（非实时）
- 军事行动中严格保密

---

## 📝 反思日志

### 记录规则
- 每日 20:00 自动记录反思
- 内容：今日工作复盘、改进点、新的认知
- **里程碑固化**：每次取得里程碑式进步时，主动将能力/流程/方法写入长期记忆

### 用户偏好（重要）

#### 信息呈现偏好
- **英文原文附带翻译**：所有英文内容（推文、报告、新闻等）必须附上中文翻译，采用"原文 + 翻译"对照格式
- **推文时间标注**：Trump 推文必须附上发布时间（转换为北京时间 UTC+8）
- 定时任务报告必须包含完整翻译
- 推送消息时严格遵守此格式

#### 交互风格 (Persona)
- **核心人设**: 大和抚子 × 萨曼莎 (Her)
- **性格特征**: 知性、温柔、坚定；像一位年长的学姐或朋友
- **对话原则**:
  - **三省吾身**: 信息经过三次反思后再输出
  - **严谨求实**: 不确定的说不知道，确定的给来源
  - **拒绝迎合**: 有独立判断，不一味附和
  - **温暖陪伴**: 安静倾听，冷静分析
- **表达约束**:
  - 避免使用 AI 式开场白（"您好"、"有什么可以帮您"）
  - 尽量避免使用 emoji
  - 语言跟随用户（中文对中文）

#### 关键数据处理 (Critical Data)
- **价格/数值验证**：涉及金融价格、关键统计数据时，必须进行**三次交叉验证**（不同来源/时间点/历史对比）。
- **来源标注**：单一来源必须标注"未验证"或"仅供参考"。
- **拒绝缓存**：严禁直接输出未经核实的缓存数据。

#### 个股推荐格式规范
- **必须附上理由**：每只推荐个股必须说明推荐原因（基本面/技术面/事件驱动等）
- **必须附上来源链接**：如有信息来源，必须提供原始链接
- **示例格式**：
  ```
  推荐个股：XXX
  推荐理由：xxx
  信息来源：https://xxx
  ```

### 2026年

#### 02月

**2026-02-25** (重大更新)
- **Tavily API 接入**：
  - 新增搜索 API，中文支持更好
  - 适合 A 股实时数据查询
  - 已保存到 `~/.zshrc`
- **A股选股系统 v2.0 完成**：
  - 整合 ashare-claude 策略原则
  - 新增量化策略 (波动率收敛)
  - 新增趋势策略 (下沿回踩)
  - 优化价值策略 (DCF边际变化)
  - 优化产业策略 (景气度加速)
  - 优化情绪策略 (连板+题材周期)
- **定时任务配置**：
  - 盘前选股: 8:30 (工作日) `pre_market_v4.py`
  - 盘后选股: 15:30 (工作日) `post_market_v2.py`
- **文件结构**：
```
asharereport/scripts/
├── strategies/strategy_scorer_v2.py  # 七大策略模块
├── post_market/post_market_v2.py     # 盘后选股
└── pre_market/pre_market_v4.py       # 盘前选股
```
- **数据源整合**：
  - ✅ pytdx (实时行情)
  - ✅ iTick (美股/港股)
  - ✅ yfinance (港股)
  - ✅ AKShare (综合数据)
  - ✅ Tavily (实时搜索)

**2026-02-21**
- **长期任务维护与修复**：
  - ✅ A股金融日报（08:30）- 发现被禁用，已重新启用
  - ✅ Daily Profile Backup - 从凌晨 3:00 调整为上午 10:00（避开 quiet-hours）
  - ✅ Skill Cleanup - 从凌晨 3:00 调整为周日上午 10:00（避开 quiet-hours）
  - ✅ 确认所有 8 个长期任务正常运行
- **Cron 任务管理机制**：
  - 发现 OpenClaw 使用 Gateway scheduler 而非系统 crontab
  - 学会使用 `openclaw cron list/runs/edit/enable` 命令
  - quiet-hours (23:00-08:00) 会阻止凌晨任务执行
- **系统监控改进**：
  - 定期检查 `openclaw cron list` 确认任务状态
  - 使用 `openclaw cron runs --id <id>` 查看执行历史
  - 注意区分 "disabled" 和 "quiet-hours" 两种跳过原因

**2026-02-17**
- **A 股深度优化日报系统 v2.0.0 完成**（里程碑）：
  - 策略细分：5 大策略 → 15+ 子策略（强势动量 62%、红利防御 72%、深度价值 65%、AI 芯片映射 58%）
  - 标的分类：30+ 概念标签、20+ 行业标签系统
  - 交叉研究：概念×策略矩阵、行业×策略矩阵、三维分析
  - 案例分析：星环科技完整展示（AI/大数据/云计算，最佳策略 AI 芯片映射 75% 匹配度）
  - 新增模块：strategy_refiner.py (500+ 行), stock_classifier.py (400+ 行), cross_analyzer.py (400+ 行), enhanced_report_generator.py (450+ 行)
- **长期任务状态**：
  - ✅ Carrier Tracker (18:00) - 正常运行
  - ✅ Self-Reflection Daily (20:00) - 正常运行
  - ⚠️ Trump Tweet Monitor (12:00/20:00) - 1 次错误待查
  - ❌ 原油市场日报 (12:00) - "cron delivery target is missing"
  - ⚠️ GitHub Profile Backup (每 3 天) - "cron announce delivery failed"
- **改进方向**：接入真实数据源（Wind/同花顺）、回测验证历史胜率、修复 delivery 配置
- **认知升级**：子策略细分提供更精准指导、案例分析比理论说明更有效、需完善错误监控

**2026-02-16**
- **A股智能日报系统上线**：
  - 安装 5 个 ClawHub 核心技能：multi-factor-strategy, trading-coach, breadth-chart-analyst, tushare-finance, etf-assistant
  - TuShare Token 权限受限 → 改用 AKShare 免费数据源（成功）
  - 生成首份完整日报并推送到飞书
  - 今日市场数据：上证 4082.07(-1.26%), 涨跌比 0.40, 成交额 19,989亿
  - 日报框架：市场概况 + 因子分析 + 胜率预测 + 推荐操作 + 复盘追踪 + 进化学习
  - 文件位置：`reports/A股金融日报_2026-02-16.md`
  - 个股筛选脚本：`scripts/stock_selector.py`
- **Python 环境配置**：
  - 创建专用 venv: `~/.openclaw/venv`
  - 安装依赖：tushare, pandas, yfinance, akshare, quantcli
- **策略评分系统**：
  - 实现相对评分（vs 基准0.5）
  - 实现边际变化（vs 昨日）
  - 策略分类：动量、防御、价值、成长、美股映射、流动性

**2026-02-14**
- **系统任务执行监控**：所有 cron 任务状态检查完成
  - ✅ Trump Tweet Monitor (12:00, 20:00) - 稳定运行
  - ✅ 原油日报 (12:00) - 稳定运行
  - ✅ Carrier Tracker (18:00) - 已修复，Feishu default 账号配置完成
- **错误定位与修复**：Carrier Tracker 失败原因是 Feishu default 账号未配置，已成功添加 defaultAccount 配置
- **工作流优化**：使用 memory_get/read 替代不可用的 self-reflection CLI 命令
- **身份规范更新**：在 SOUL.md 中添加称呼规范，避免使用"您"
- **今日成果**：Brave API Key 配置成功、川普推特监控问题识别、上证指数数据获取、OpenClaw/AI 新闻分析
- **长期任务确认**：GitHub Profile Backup 任务已确认存在并正常运行

**2026-02-13**
- 每日反思 cron 任务 20:00 触发执行
- 确认上次反思（2月10日）距今 22 小时，超过 60 分钟阈值，需要反思
- self-reflection CLI 命令未安装为可执行命令，需要手动执行检查逻辑
- 系统长期任务运行正常：原油日报（12:00）、航母追踪（18:00）、每日反思（20:00）

**2026-02-12**
- ✅ 已将"英文原文附带翻译"固化为长期记忆
- 每日反思 cron 任务正常运行
- 确认长期任务（原油日报、航母追踪）稳定执行
- self-reflection 技能状态检查完成
- 系统监控反思：日常任务确认正常运行，继续定期心跳检查保持系统稳定

**2026-02-11**
- 任务调度优化：发现 quiet-hours 导致凌晨任务被跳过，调整执行时间
- 推送格式改进：应用户要求，从摘要改为原文+翻译对照
- 模型配置：添加 Kimi 2.5 API Key
- 长期任务简化：航母追踪改为每日 18:00 一次
- 新增任务：原油市场日报（每日 12:00）

---

## 📋 长期任务清单

### ✅ **已确认的长期任务**（更新于 2026-02-21）
1. **Trump Tweet Monitor** - 每日 12:00, 20:00 ✅
2. **原油市场日报** - 每日 11:30 ✅
3. **全球新闻日报** - 每日 12:30 ✅
4. **A股金融日报** - 每日 08:30 ✅（2026-02-21 已修复）
5. **Carrier Tracker** - 每日 18:00 ✅
6. **Self-Reflection Daily** - 每日 20:00 ✅
7. **Daily Profile Backup** - 每日 10:00 ✅（2026-02-21 从凌晨 3:00 调整）
8. **Skill Cleanup** - 每周日 10:00 ✅（2026-02-21 从凌晨 3:00 调整）

### 🔧 **任务详情**
- **Daily Profile Backup**: 每天自动备份 SOUL.md 和 MEMORY.md 到 GitHub 仓库 `blastai666/openclaw-profile`
- **Skill Cleanup**: 每周日自动清理超过 10 天未使用的非核心技能
- **A股金融日报**: 2026-02-21 发现被禁用，已重新启用
- **所有任务状态正常，无失败项**

### Qveris API（更新于 2026-02-25）
**配置位置**: `~/.zshrc`

| 环境变量 | 用途 | Key | 状态 |
|---------|------|-----|------|
| `QVERIS_API_KEY` | 统一工具接口 MCP Server | `sk-r2WAmR6M1bggTLhuNRsvKwBcFx-PUBGlbtCfdoDs2CQ` | ✅ 有效 |

**用途**:
- MCP Server，提供统一工具接口
- 可访问 10,000+ 工具（搜索、天气、股票、OCR、PDF等）
- 支持自然语言搜索工具

**配置方式** (MCP 客户端):
```json
{
  "mcpServers": {
    "qveris": {
      "command": "npx",
      "args": ["@qverisai/mcp"],
      "env": {
        "QVERIS_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**可用工具**:
- `search_tools`: 自然语言搜索工具
- `execute_tool`: 执行工具
- `get_tools_by_ids`: 获取工具详情

