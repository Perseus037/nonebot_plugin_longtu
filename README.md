<div align="center"> 
  
  <img src="https://github.com/Perseus037/data/blob/master/longtu.png?raw=true" alt="2024年是龙年...我都准备好了" width="280" height="280">

# nonebot-plugin-longtu


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
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-longtu">
  <img src="https://img.shields.io/pypi/v/nonebot-plugin-longtu.svg" alt="pypi">
</a>
<a href="https://pypi.org/project/nonebot-plugin-longtu/">
  <img src="https://img.shields.io/pypi/dm/nonebot-plugin-longtu.svg" alt="pypi download">
</a>


</div>

## 💬 前言

2024年是龙年...我都准备好了.jpg

## 📖 介绍

一个非常简单的nonebot2插件，输入指令后会从神秘的龙图仓库（内含1500张精选龙图）中随机发送一张或多张（~~可爱~~）的龙图.

ps：攻击性较强，请酌情使用。

神秘的龙图仓库：https://git.acwing.com/Est/dragon

## 💿 安装

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

在 nonebot2 项目的 `.env` 文件中添加下表中的配置

|            配置项            | 必填 | 默认值  |                                         说明                                          |
| :--------------------------: | :--: | :-----: | :-----------------------------------------------------------------------------------: |
|        `MAX_DRAGONS`         |  否  | `5`  |                              一次最大发送龙图的数量                              |

## 🎉 使用

现有指令列表：

dragon，龙龙，龙图：发送一张可爱的龙龙图片

龙图 3：发送三张可爱的龙龙图片

示例：<img src="https://github.com/Perseus037/data/blob/master/nonebot_plugin_longtu%20example.png" alt="示例" >

## 📞 制作者

### 黑纸折扇 [Perseus037] (https://github.com/Perseus037)

- QQ: 1209228678

### Whike [Whiked] (https://github.com/Whiked)

- QQ: 274752001

## 🙏 感谢

student_2333 (https://github.com/lgc2333) 的无私帮助。

## 📝 更新日志

### 0.1.1.post1

- 实现多张龙图发送
- 增加新配置项


### 0.1.0.post4

- 增加了更多类型的httpx错误处理
- 修改FinishedException位置

### 0.1.0.post1-0.1.0.post3

- 仓库内由测试的50张龙图扩展到了1500张精选龙图，随机范围更广（~~攻击性更强~~）。
- 常规修正
