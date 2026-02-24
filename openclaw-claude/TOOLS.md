# TOOLS.md - Architect's Toolkit

## 🎯 核心技能清单

### 💹 金融分析工具链

#### 数据获取
- **AKShare**: A 股实时/历史数据（东方财富、新浪财经）
- **Yahoo Finance**: 美股数据、全球市场数据
- **Tushare Pro**: 专业金融数据（需 Token）
- **备用方案**: 网页爬虫（BeautifulSoup + requests）

#### 量化分析
- **pandas**: 数据处理和时间序列分析
- **numpy**: 数值计算和矩阵运算
- **scipy**: 统计函数和优化算法
- **TA-Lib**: 技术指标库（MA、RSI、MACD、布林带等）

#### 回测框架
- **Backtrader**: 专业回测引擎
- **自研框架**: 基于 pandas 的轻量级回测
- **性能指标**: 胜率、收益率、夏普比率、最大回撤

#### 可视化
- **matplotlib**: 基础图表
- **plotly**: 交互式图表
- **seaborn**: 统计可视化

### 💻 编程工具链

#### Python 生态
- **版本**: Python 3.8+
- **虚拟环境**: venv / conda
- **包管理**: pip / poetry
- **代码质量**: black (格式化) + pylint (检查)

#### 数据存储
- **SQLite**: 轻量级本地数据库
- **CSV**: 数据备份和交换
- **JSON**: 配置文件和结构化数据
- **Parquet**: 高性能列式存储（大数据场景）

#### 版本控制
- **Git**: 代码版本管理
- **备份策略**: 桌面备份 + GitHub 同步

### 🏗️ 系统设计工具

#### 架构设计
- **模块化设计**: 数据层、策略层、回测层、输出层分离
- **接口设计**: 清晰的 API 定义
- **配置管理**: JSON/YAML 配置文件
- **日志系统**: logging 模块 + 分级日志

#### 自动化
- **定时任务**: cron (Linux/macOS) / Task Scheduler (Windows)
- **OpenClaw**: 任务调度和消息推送
- **错误处理**: try-except + 异常日志 + 告警机制

#### 性能优化
- **向量化计算**: pandas/numpy 替代循环
- **并行处理**: multiprocessing / concurrent.futures
- **缓存机制**: functools.lru_cache / 文件缓存
- **性能分析**: cProfile / line_profiler

## 📊 A 股日报系统专用配置

### 数据源配置
```python
# AKShare - 免费，无需 Token
import akshare as ak

# Tushare Pro - 需要 Token（已配置在 MEMORY.md）
import tushare as ts
ts.set_token('YOUR_TOKEN')  # 从 MEMORY.md 读取
```

### 本地数据路径
```
~/Desktop/openclaw-oai-complete-backup-2026-02-24_1308/ashare/
├── backtest_data/          # 5484 个历史 K 线 CSV
├── concept_data/           # 概念映射数据
├── price_data/             # 最新价格数据
├── reports/                # 生成的日报
└── scripts/                # 策略脚本
```

### 关键脚本
- `strategy_v3_tech_only.py` - 纯技术指标策略（15KB）
- `generate_today_recommendations_tech.py` - 今日推荐生成
- `stock_selector_v*.py` - 历史版本（v1-v6）

### 技术指标参数
```python
# 均线系统
MA_SHORT = [5, 10, 20]
MA_LONG = [60, 120, 250]

# RSI 参数
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# 布林带参数
BOLL_PERIOD = 20
BOLL_STD = 2

# 波动率参数
VOL_SHORT = 10
VOL_LONG = 30
```

## 🔧 开发环境

### 工作区
- **主工作区**: `~/.openclaw/workspace-ai5/`
- **备份位置**: `~/Desktop/openclaw-oai-complete-backup-2026-02-24_1308/`
- **GitHub 同步**: `~/Desktop/openclaw-oai-github/`

### 常用命令
```bash
# 生成今日推荐
python generate_today_recommendations_tech.py

# 运行回测
python backtest_strategy.py --start 2023-01-01 --end 2024-12-31

# 查看日志
tail -f logs/ashare_$(date +%Y%m%d).log

# 数据更新
python scripts/update_price_data.py
```

## 📝 工作流程

### 每日流程
1. **08:00** - 自动获取最新交易日数据
2. **08:30** - 生成今日推荐（15-20 只股票）
3. **09:00** - 推送到飞书
4. **15:30** - 盘后复盘（T+N 收益统计）
5. **20:00** - 更新 MEMORY.md（重要发现）

### 每周流程
1. **周日 20:00** - 生成周报
2. **周日 20:30** - 策略效果评估
3. **周日 21:00** - 参数自动调优（如需要）

### 紧急情况
- **数据异常**: 检查 API 状态 → 切换备用数据源
- **策略失效**: 暂停推荐 → 分析原因 → 调整参数
- **系统故障**: 查看日志 → 恢复备份 → 重启服务

## 🎓 持续学习资源

### 量化投资
- BigQuant 量化平台
- 聚宽（JoinQuant）
- 优矿（Uqer）
- QuantConnect

### 技术指标
- Investopedia - 技术分析教程
- TradingView - 图表和指标
- TA-Lib 文档

### 学术论文
- SSRN (Social Science Research Network)
- arXiv - 量化金融分类
- Journal of Financial Economics

---

**最后更新**: 2026-02-24 23:35  
**维护者**: Architect  
**版本**: v1.0
