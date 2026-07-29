# 安装说明

## 文件放置

将压缩包内的所有文件和文件夹上传到公开仓库 `Quartzsyr/Quartzsyr` 的根目录，并覆盖原有 `README.md`。

目录应为：

```text
Quartzsyr/
├── README.md
├── README_CN.md
├── SETUP_CN.md
├── assets/
├── scripts/
└── .github/
    └── workflows/
        └── profile-assets.yml
```

## 启用自动更新

1. 打开仓库 `Settings`。
2. 进入 `Actions` → `General`。
3. 在 `Workflow permissions` 中选择 `Read and write permissions`。
4. 保存设置。
5. 打开仓库的 `Actions` 页面。
6. 选择 `Refresh profile assets`。
7. 点击 `Run workflow`。

首次运行完成后，下面这些文件会自动更新：

- `assets/stats-dark.svg`
- `assets/stats-light.svg`
- `assets/languages-dark.svg`
- `assets/languages-light.svg`
- `assets/streak-dark.svg`
- `assets/streak-light.svg`
- `assets/snake.svg`
- `assets/snake-dark.svg`

工作流每天自动执行一次。所有 README 图片均来自当前仓库，不依赖 Vercel、Shields、Skillicons 或其他图片接口。

## 中英文切换

- `README.md` 为英文主页，也是 GitHub 个人主页默认显示内容。
- `README_CN.md` 为中文版本。
- 两个文件顶部使用相对链接进行切换。

## 修改排除仓库

语言统计默认排除部分旧仓库。可在 `.github/workflows/profile-assets.yml` 中修改：

```yaml
EXCLUDED_REPOS: Quartzsyr,Quartzsyr.github1,Quartzsyr.github,5,4,8888,Quartz-syr
```
