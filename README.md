<div align="center">

# nonebot-plugin-longtu

![你变的很二次元.jpg（](Cutelong.jpg)

_✨一个随机发送龙图的nonebot2插件✨_

<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
<a href="https://pdm.fming.dev">
  <img src="https://img.shields.io/badge/pdm-managed-blueviolet" alt="pdm-managed">
</a>
<!-- <a href="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/f4778875-45a4-4688-8e1b-b8c844440abb">
  <img src="https://wakatime.com/badge/user/b61b0f9a-f40b-4c82-bc51-0a75c67bfccf/project/f4778875-45a4-4688-8e1b-b8c844440abb.svg" alt="wakatime">
</a> -->

<br />

<a href="./LICENSE">
  <img src="https://img.shields.io/github/license/lgc-NB2Dev/nonebot-plugin-uma.svg" alt="license">
<a href="https://pypi.python.org/pypi/nonebot-plugin-longtu">
</a>

</div>

## 💬 前言

2024年是龙年，能不能来点喜庆的龙图（

## 📖 介绍

一个非常简单的nonebot2插件，输入指令后会从神秘的龙图仓库（内含1500张精选龙图）中随机发送一张（~~可爱~~）的龙图.

现在只有最基础的功能，最近又太忙，等以后有空的时候写点好玩的新功能。

ps：攻击性较强，请酌情使用。

神秘的龙图仓库：https://git.acwing.com/Est/dragon

## 💿 安装
没发包，目前只能通过git clone下载使用

下载完成后将插件文件夹扔进nonebot2\.venv\Lib\site-packages根目录中
然后打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分的 `plugins` 项里追加写入nonebot_plugin_longtu即可

<!--
<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-longtu
```
-->

</details>

<details open>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>pip</summary>

```bash
pip install nonebot-plugin-longtu
```

</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-longtu
```

</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-uma
```

</details>
<details>
<summary>conda</summary>

```bash
conda install nonebot-plugin-longtu
```

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分的 `plugins` 项里追加写入

```toml
[tool.nonebot]
plugins = [
    # ...
    "nonebot_plugin_longtu"
]
```

</details>

## ⚙️ 配置

暂无

## 🎉 使用

现有指令列表：

dragon，龙龙，龙图：发送一张可爱的龙龙图片

示例：<img src="https://github.com/Perseus037/data/blob/master/nonebot_plugin_longtu%20example.png" alt="示例" >

## 📞 制作者

### 黑纸折扇 [Perseus037] (https://github.com/Perseus037)

- QQ: 1209228678

### Whike [Whiked] (https://github.com/Whiked)

- QQ: 274752001

## 🙏 感谢

student_2333 (https://github.com/lgc2333) 对于我学习编写插件和配置qqbot过程中的无私帮助。

## 📝 更新日志

### 0.1.1

- 仓库内由测试的50张龙图扩展到了1500张精选龙图，随机范围更广（~~攻击性更强~~）。
