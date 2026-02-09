# 数据流与Schema设计：AI驱动全自动化选题决策系统

## 核心实体定义
1. **TopicSuggestion（选题建议）**：系统生成的核心决策单元，用户直接使用的内容
2. **HotTrendData（热点趋势数据）**：从各平台爬取的热点话题、关键词热度数据
3. **CrawlerTask（爬虫任务）**：记录每次爬虫任务的状态、平台、工具使用情况
4. **UserConfig（用户配置）**：用户设置的系统运行参数
5. **PerformanceMetric（效果指标）**：记录选题对应的涨粉数据，用于优化AI决策

## 数据结构 (JSON Schema)
### 1. TopicSuggestion
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "选题唯一标识，UUID生成"
    },
    "title": {
      "type": "string",
      "description": "选题标题（如“2024年必入的5款平价防晒”）"
    },
    "growth_potential": {
      "type": "string",
      "enum": ["high", "medium", "low"],
      "description": "涨粉潜力等级"
    },
    "content_format": {
      "type": "string",
      "enum": ["short_video", "image_text", "long_video", "official_account_article"],
      "description": "适配的内容格式"
    },
    "audience_tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "核心受众标签数组（如[\"Z世代\", \"美妆爱好者\", \"学生党\"]）"
    },
    "platforms": {
      "type": "array",
      "items": {"type": "string", "enum": ["xiaohongshu", "bilibili", "wechat_official"]},
      "description": "适配的平台数组"
    },
    "priority": {
      "type": "integer",
      "minimum": 1,
      "description": "优先级排序（1为最高）"
    },
    "data_sources": {
      "type": "array",
      "items": {"type": "string"},
      "description": "生成该选题参考的数据源（如[\"xiaohongshu_hot\", \"bilibili_comment\"]）"
    },
    "create_time": {
      "type": "string",
      "format": "date-time",
      "description": "选题生成时间"
    },
    "missing_data_notes": {
      "type": "string",
      "nullable": true,
      "description": "数据缺失说明（如“未获取B站竞品数据”）"
    }
  },
  "required": ["id", "title", "growth_potential", "content_format", "audience_tags", "priority", "create_time"]
}
```

### 2. CrawlerTask
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "爬虫任务唯一标识"
    },
    "platform": {
      "type": "string",
      "enum": ["xiaohongshu", "bilibili", "wechat_official"]
    },
    "crawler_tool": {
      "type": "string",
      "enum": ["coze_workflow", "scrapy", "requests"],
      "description": "使用的爬虫工具"
    },
    "status": {
      "type": "string",
      "enum": ["success", "failed", "pending"],
      "description": "任务状态"
    },
    "retry_count": {
      "type": "integer",
      "minimum": 0,
      "description": "重试次数"
    },
    "error_message": {
      "type": "string",
      "nullable": true,
      "description": "失败错误信息"
    },
    "start_time": {
      "type": "string",
      "format": "date-time"
    },
    "end_time": {
      "type": "string",
      "format": "date-time",
      "nullable": true
    }
  },
  "required": ["task_id", "platform", "crawler_tool", "status", "start_time"]
}
```

## 数据流转图 (Data Flow)
```
1. 数据源层 → 爬虫层：
   小红书/B站/微信公众号公开数据 → 多引擎爬虫（自动切换工具）→ 原始非结构化数据

2. 爬虫层 → ETL层：
   原始非结构化数据 → 数据清洗（去重、格式转换）→ 热点识别（关键词热度统计）→ 受众标签提取（NLP分析）→ 结构化数据

3. ETL层 → 存储层：
   结构化数据 → 极致了数据平台（长期存储）→ SQLite缓存（临时存储）

4. 存储层 → AI决策引擎：
   结构化热点数据、受众标签 → GPT-4o大模型 → 带优先级的选题建议 → 结构化选题数据

5. AI决策引擎 → 推送层：
   结构化选题数据 → 消息模板渲染 → 飞书/微信/邮件 → 用户接收选题清单

6. 用户反馈 → 优化层：
   用户选择的选题、涨粉数据 → 数据存储层 → AI决策模型微调 → 提升未来选题准确性
```

## 埋点与可观测性 (Analytics Plan)
### 关键事件埋点
1. `crawler_start`：爬虫任务启动时触发，记录平台、工具、时间
2. `crawler_switch`：爬虫工具自动切换时触发，记录原工具、目标工具、切换原因
3. `crawler_failed`：爬虫任务失败时触发，记录平台、工具、错误信息
4. `topic_generated`：选题建议生成时触发，记录选题ID、涨粉潜力、优先级
5. `topic_pushed`：选题清单推送成功时触发，记录推送渠道、推送时间、选题数量
6. `topic_clicked`：用户点击选题卡片时触发，记录选题ID、点击时间
7. `growth_tracked`：选题对应的涨粉数据上报时触发，记录选题ID、涨粉数量、统计时间

### 核心监控指标
1. 爬虫成功率：成功爬虫任务数/总任务数 × 100%
2. 推送准时率：准时推送次数/总推送次数 × 100%
3. 选题点击率：用户点击选题数/推送选题总数 × 100%
4. 选题涨粉转化率：带来涨粉的选题数/用户选择的选题数 × 100%
5. 平均选题生成耗时：从爬虫启动到选题生成的平均时间

## 隐私与合规
1. **爬虫合规**：
   - 严格遵守各平台`robots.txt`协议，仅爬取公开可访问的非隐私数据
   - 设置合理的请求频率（如每10秒1次），避免对平台服务器造成压力
   - 爬虫UA标识设置为合法的浏览器标识，避免被平台识别为恶意爬虫

2. **数据脱敏**：
   - 对爬取的用户评论数据，仅提取情感倾向、关键词等结构化信息，不存储原始评论内容
   - 不爬取或存储用户个人隐私信息（如手机号、地址、私人账号信息）

3. **数据留存**：
   - 热点数据、爬虫日志留存30天，到期自动删除
   - 选题建议、涨粉数据留存至用户账号注销或主动删除

4. **用户知情权**：
   - 在后台配置页面明确告知用户系统爬取的数据范围、使用目的
   - 提供数据导出与删除功能，用户可随时导出或删除自己的所有数据