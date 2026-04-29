# Ads 周报工具包 v0.1

一个面向 Meta Ads 场景的轻量 Python CLI 工具，可以把广告报表 CSV 快速整理成可分享的周报交付包。

这个仓库同时保留了两部分内容：

- `ads-weekly-report-kit/`：可编辑、可运行的项目源码
- `ads-weekly-report-kit_v0.1.zip`：当前版本的打包压缩包

## 这个项目能做什么

典型使用流程非常简单：

1. 从 Meta Ads Manager 导出 CSV 报表
2. 运行一条命令
3. 自动得到 HTML 周报和 Excel 清洗结果

生成产物包括：

- `weekly_report.html`：适合直接分享的单文件周报
- `clean.xlsx`：适合进一步分析的清洗后明细与汇总表

## 项目亮点

- 聚焦 Meta Ads CSV，范围克制，适合 v0.1 产品化
- 自动生成 KPI 摘要、趋势图、Top 表格、异常提示
- 支持 Excel 清洗导出，便于二次分析
- 使用 YAML 做字段映射，适配不同导出列名
- 如果存在有效日期列，默认自动取最近 7 天
- 自带基础 smoke tests

## 仓库结构

```text
.
|-- README.md
|-- .gitignore
|-- ads-weekly-report-kit_v0.1.zip
`-- ads-weekly-report-kit/
    |-- README.md
    |-- QUICKSTART.md
    |-- CHANGELOG.md
    |-- requirements.txt
    |-- pyproject.toml
    |-- examples/
    |-- handbook/
    |-- outputs/
    |-- templates/
    |-- tests/
    `-- src/
```

## 主要交付物

在 `ads-weekly-report-kit/outputs/` 中可以看到：

- `weekly_report.html`：可直接查看或发给客户/同事的周报页面
- `clean.xlsx`：包含清洗后的明细数据和汇总表

## 快速运行

进入 `ads-weekly-report-kit/` 目录后执行：

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
adswk report --input examples/meta_sample.csv --output outputs/ --template meta_ads --level campaign
```

## 建议阅读入口

- 项目说明：`ads-weekly-report-kit/README.md`
- 快速开始：`ads-weekly-report-kit/QUICKSTART.md`
- Meta 导出说明：`ads-weekly-report-kit/handbook/META_EXPORT_GUIDE.md`
- 常见问题：`ads-weekly-report-kit/handbook/FAQ.md`

## 说明

- 压缩包 `ads-weekly-report-kit_v0.1.zip` 会一并保留并上传
- 本地环境目录例如 `.venv/` 不应提交到 GitHub 历史中
