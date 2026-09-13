# Profile 维护说明

英文主页为 `README.md`，中文页为 `README_CN.md`。页头使用本地 SVG 动画，支持系统减少动态效果设置。统计卡片按系统深浅色自动切换，不依赖第三方图片服务。

## 自动更新

- `Refresh profile assets`：每日 01:15 UTC（北京时间 09:15），更新概览、语言分布及年度贡献。修改生成脚本也会触发，可在 Actions 手动运行。使用内置 `GITHUB_TOKEN`，无需新增密钥。
- `Generate Snake`：沿用现有每日工作流，生成 `dist/github-snake*.svg`；README 已与此路径对齐。
- `Generate Metrics`：沿用现有 `METRICS_TOKEN` 与工作流，更新折叠区的详细分析。

工作流需有仓库内容写入权限。任一数据请求失败或贡献日历解析不完整时，统计生成任务报错，保留现有图片，可在 Actions 查看失败原因。

## 统计口径

- 仓库、Star、Fork：公开、自有、非 fork 仓库；Followers 为公开关注者数。
- 语言：公开、自有、未归档仓库的代码字节占比，排除 Profile 仓库；显示前六名与 Other。不是熟练度，也不是使用时长。
- 贡献：GitHub 公开个人贡献日历显示的最近一年数据；可能包含用户已选择公开的私有贡献数量，不获取私有仓库内容。不是 commit 数。
- 活跃天数：周期内贡献数大于零的天数。最长连续天数仅在展示周期内计算。最近 30 天包含日历最后一天。
- 趋势：从日历起点每七天合计，最后一组可能不足七天。

可在工作流设置 `EXCLUDED_REPOS`（逗号分隔）调整语言统计排除项，默认 `Quartzsyr`。本地运行：`python3 scripts/generate_profile_assets.py`，无需额外依赖。
