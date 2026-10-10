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

神秘的龙图仓库：https://github.com/Whiked/Dragonimg

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
poetry add nonebot-plugin-longtu
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
| `LONGTU_MODE` | 否 | `local` | `local` 从完整索引选图，优先读取选中图片的本地缓存；`remote` 每次从远程取图，不写本地缓存 |
| `LONGTU_LOCAL_DIR` | 否 | 插件目录下的 `images` | 本地图片目录，支持绝对路径；相对路径基于 bot 启动目录 |
| `LONGTU_AUTO_DOWNLOAD` | 否 | `true` | 本地模式下，在后台逐渐补齐图片库 |
| `LONGTU_REMOTE_FALLBACK` | 否 | `true` | 选中图片的本地缓存缺失或损坏时下载同一张并缓存；关闭后只从本地缓存池选图 |
| `LONGTU_DOWNLOAD_CONCURRENCY` | 否 | `3` | 后台每批最多并行下载的图片数，范围 1～8 |
| `LONGTU_DOWNLOAD_INTERVAL` | 否 | `0.1` | 后台每批成功下载后的等待秒数，可设为 0 |
| `LONGTU_IDLE_SECONDS` | 否 | `3` | 龙图请求结束后等待多久再继续后台下载 |
| `LONGTU_STARTUP_DELAY` | 否 | `5` | 启动后延迟多少秒开始后台同步 |
| `LONGTU_TIMEOUT` | 否 | `8` | 单次 HTTP 操作超时秒数 |
| `LONGTU_REQUEST_TIMEOUT` | 否 | `20` | 一次命令读取图片的累计等待上限秒数，不含 QQ 发送耗时 |

### 默认本地模式

不添加配置即可使用。每次先从完整索引随机选图，选中的图片已有本地缓存就直接读取，缺失或损坏则下载同一张并缓存；下载失败继续尝试其他候选，直到成功、候选耗尽或达到请求超时。后台分批并行补库，因此缓存尚未补齐时随机范围也不受本地图片数量限制，但未缓存的图片需要等待下载。关闭 `LONGTU_REMOTE_FALLBACK` 后只从本地缓存池随机选图，不进行前台远程下载。一次命令在图片数量足够时不会重复抽取。

“空闲”指没有龙图请求正在处理，且距离最近一次龙图请求结束超过指定时间，不是检测整机 CPU 或整个群是否安静。已经发起的一批下载会完成，后续批次等待前台请求结束。默认 3 张并行、批次间隔 0.1 秒，1516 张图片的批次间隔合计约 51 秒。实际完成时间还取决于网络、使用频率和失败重试，不能将间隔之和当作总耗时。HTTP 连接池另为前台预留容量。

内置 `index.json` 固定记录 1516 张图片的真实文件名、大小和 Git blob 校验值。随机取图与后台下载共用这份索引。失败批次按 5、10、20、40、60 秒退避，成功批次恢复正常速度；后续轮次只重试失败项，重启后跳过已完整保存的图片。全部下载完成后后台任务退出，不持续轮询。下载使用临时文件并校验后替换，不自动删除本地图。图片只在使用时读入内存，不把整个图库常驻内存。

希望更快补库时可将 `LONGTU_DOWNLOAD_CONCURRENCY=5`、`LONGTU_DOWNLOAD_INTERVAL=0`；带宽较小时可设并发为 1 并增加批次间隔。旧配置中的显式等待值会继续生效，升级后需移除或调整才能使用新默认值。

自定义目录示例：

```dotenv
LONGTU_MODE=local
LONGTU_LOCAL_DIR="./data/longtu"
```

也可以下载 [Dragonimg](https://github.com/Whiked/Dragonimg) 的 ZIP，将 `drimg` 内图片放入该目录，保持文件名不变。启动时仅收录本层索引内的图片；运行期间手动补入图片后重启 bot。默认插件目录不可写时，请设置可写目录，尤其是容器或系统级安装环境；容器建议挂载该目录，升级插件前也建议备份本地图片。图库若将来变化，需要维护者同步更新并发布索引。

完全离线使用已有图片：

```dotenv
LONGTU_MODE=local
LONGTU_LOCAL_DIR="./data/longtu"
LONGTU_AUTO_DOWNLOAD=false
LONGTU_REMOTE_FALLBACK=false
```

### 纯远程模式

```dotenv
LONGTU_MODE=remote
```

此模式使用插件内置清单，每次下载图片字节发送，不创建本地图片目录，不运行后台补库；更新内置清单随插件升级。它仍依赖 GitHub 网络，网络较差时建议使用默认本地模式。

两种模式都发送图片字节，适用于 NoneBot 与 OneBot 协议端位于不同机器的环境，不要求协议端能访问 NoneBot 的本地路径。

## 🎉 使用

现有指令列表：

dragon，龙龙，龙图：发送一张可爱的龙龙图片

龙图 n：发送n张可爱的龙龙图片（默认n最大为5，可通过.env配置调整MAX_DRAGONS参数实现n的最大值调整，允许配置范围为1-50）

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

### 0.2.1
- 默认后台 3 张并行，启动等待 5 秒、请求后空闲 3 秒、每批间隔 0.1 秒。
- 前台请求优先，失败批次指数退避，仅重试失败图片，保留校验与重启续传。

### 0.2.0
- 支持本地、远程两种模式，默认本地优先，目录可配置。
- 空闲时单文件渐进下载，已有图片可立即使用，支持重启续传，补齐后自动结束。
- 内置真实图片清单，校验下载内容，限制请求等待，复用 HTTP 连接。

### 0.1.2
- 龙库换源：将图片资源迁移到 GitHub Raw（Whiked/Dragonimg/drimg/），提升可用性与稳定性

### 0.1.1.post1

- 实现多张龙图发送
- 增加新配置项

### 0.1.0.post4

- 增加了更多类型的httpx错误处理
- 修改FinishedException位置

### 0.1.0.post1-0.1.0.post3

- 仓库内由测试的50张龙图扩展到了1500张精选龙图，随机范围更广（~~攻击性更强~~）。
- 常规修正
