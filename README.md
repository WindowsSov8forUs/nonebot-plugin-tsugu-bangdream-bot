<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# NoneBot-Plugin-Tsugu-BanGDream-Bot

_✨ [Koishi-Plugin-Tsugu-BanGDream-Bot](https://github.com/Yamamoto-2/tsugu-bangdream-bot) 的 NoneBot2 实现 ✨_


<a href="https://github.com/Yamamoto-2/tsugu-bangdream-bot">
  <img src="https://img.shields.io/badge/tsugu bangdream bot-api-FFEE88" alt="license">
</a>
<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/WindowsSov8forUs/nonebot-plugin-tsugu-bangdream-bot.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-tsugu-bangdream-bot">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-tsugu-bangdream-bot.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

[koishi-plugin-tsugu-bangdream-bot](https://github.com/Yamamoto-2/tsugu-bangdream-bot) 的 NoneBot2 实现，旨在于 NoneBot 上还原 Tsugu Bot 的使用。

## 📖 介绍

在 NoneBot2 上进行的对于 [koishi-plugin-tsugu-bangdream-bot](https://github.com/Yamamoto-2/tsugu-bangdream-bot) 的复刻，支持跨平台，支持自定义。

> 基于 [NoneBot-Plugin-Alconna](https://github.com/nonebot/plugin-alconna) 和 [nonebot-plugin-userinfo](https://github.com/noneplugin/nonebot-plugin-userinfo) 实现跨平台支持。
>
> 基于 [tsugu-api-python](https://github.com/WindowsSov8forUs/tsugu-api-python) 实现与 Tsugu 后端的连接。

## 💿 安装

>
> ⚠ 使用警告 ⚠
>
> 若运行本插件时出现了如下异常信息：
>
> ```bash
> ImportError: Failed to import httpx and aiohttp, please install one of them to use this plugin.
> ```
>
> 表示你的 Nonebot 项目没有使用 HTTP 客户端驱动，也没有运行在安装了 `httpx` 库或 `aiohttp` 库的环境。
>
> 请确保使用了 HTTP 客户端驱动或安装了这两个库的其中一个。
>

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-tsugu-bangdream-bot

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-tsugu-bangdream-bot
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-tsugu-bangdream-bot
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-tsugu-bangdream-bot
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-tsugu-bangdream-bot
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot-plugin-tsugu-bangdream-bot"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

**nonebot-plugin-tsugu-bangdream-bot** 并无必填配置，但仍然建议对部分配置进行添加。

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| TSUGU_USE_EASY_BG | 否 | `False` | 是否使用简易背景，启用这将大幅提高速度，关闭将使部分界面效果更美观 |
| TSUGU_COMPRESS | 否 | `False` | 是否压缩图片，启用会使图片质量下降，但是体积会减小，从而减少图片传输时所需的时间 |
| TSUGU_BANDORI_STATION_TOKEN | 否 | `None` | BandoriStationToken, 用于发送车牌，可以去 [BandoriStation](https://github.com/maborosh/BandoriStation/wiki/API%E6%8E%A5%E5%8F%A3) 申请。缺失情况下，视为Tsugu车牌 |
| TSUGU_REPLY | 否 | `False` | 消息是否回复用户 |
| TSUGU_AT | 否 | `False` | 消息是否@用户 |
| TSUGU_NO_SPACE | 否 | `False` | 是否启用无需空格触发大部分指令，启用这将方便一些用户使用习惯，但会增加bot误判概率，仍然建议使用空格 |
| TSUGU_RETRIES | 否 | `3` | 重试次数配置，配置 `<= 0` 时代表关闭重试机制 |
| TSUGU_BACKEND_URL | 否 | `"http://tsugubot.com:8080"` | 后端服务器地址，用于处理指令。如果有自建服务器，可以改成自建服务器地址。默认为Tsugu公共后端服务器。 |
| TSUGU_DATA_BACKEND_URL | 否 | `"http://tsugubot.com:8080"` | 用户数据后端服务器地址，用于处理用户与车牌指令。如果有自建服务器，可以改成自建服务器地址。默认为Tsugu公共后端服务器。 |
| TSUGU_PROXY | 否 | `""` | 使用的代理服务器。在部分地区，网络环境可能无法连接后端服务器。通过此配置项配置代理服务器。 |
| TSUGU_TIMEOUT | 否 | `10` | 后端服务器的响应超时时间（秒） |
| TSUGU_BACKEND_PROXY | 否 | `False` | 是否通过代理服务器访问后端服务器 |
| TSUGU_DATA_BACKEND_PROXY | 否 | `False` | 是否通过代理服务器访问用户数据后端服务器 |
| TSUGU_OPEN_FORWARD_ALIASES | 否 | `()` | 开启车牌转发指令别名 |
| TSUGU_CLOSE_FORWARD_ALIASES | 否 | `()` | 关闭车牌转发指令别名 |
| TSUGU_BIND_PLAYER_ALIASES | 否 | `()` | 绑定玩家指令别名 |
| TSUGU_UNBIND_PLAYER_ALIASES | 否 | `()` | 解除绑定指令别名 |
| TSUGU_MAIN_SERVER_ALIASES | 否 | `()` | 切换服务器模式指令别名 |
| TSUGU_DEFAULT_SERVERS_ALIASES | 否 | `()` | 切换显示服务器列表指令别名 |
| TSUGU_PLAYER_STATUS_ALIASES | 否 | `()` | 用户玩家状态指令别名 |
| TSUGU_PLAYER_LIST_ALIASES | 否 | `()` | 用户玩家状态列表指令别名 |
| TSUGU_SWITCH_INDEX_ALIASES | 否 | `()` | 切换默认玩家 ID 指令别名 |
| TSUGU_YCM_ALIASES | 否 | `()` | 查询车牌指令别名 |
| TSUGU_SEARCH_PLAYER_ALIASES | 否 | `()` | 查询玩家指令别名 |
| TSUGU_SEARCH_CARD_ALIASES | 否 | `()` | 查卡指令别名 |
| TSUGU_CARD_ILLUSTRATION_ALIASES | 否 | `()` | 查卡面指令别名 |
| TSUGU_SEARCH_CHARACTER_ALIASES | 否 | `()` | 查角色指令别名 |
| TSUGU_SEARCH_EVENT_ALIASES | 否 | `()` | 查活动指令别名 |
| TSUGU_SEARCH_SONG_ALIASES | 否 | `()` | 查曲指令别名 |
| TSUGU_SONG_CHART_ALIASES | 否 | `()` | 查谱面指令别名 |
| TSUGU_SONG_RANDOM_ALIASES | 否 | `()` | 随机曲目指令别名 |
| TSUGU_SONG_META_ALIASES | 否 | `()` | 查歌曲分数表指令别名 |
| TSUGU_EVENT_STAGE_ALIASES | 否 | `()` | 查试炼舞台指令别名 |
| TSUGU_SEARCH_GACHA_ALIASES | 否 | `()` | 查卡池指令别名 |
| TSUGU_YCX_ALIASES | 否 | `()` | 查询预测线指令别名 |
| TSUGU_YCX_ALL_FORWARD_ALIASES | 否 | `()` | 查询全榜预测线指令别名 |
| TSUGU_LSYCX_ALIASES | 否 | `()` | 查询历史预测线指令别名 |
| TSUGU_GACHA_SIMULATE_ALIASES | 否 | `()` | 抽卡模拟指令别名 |

## 🎉 使用

参考 [关于 Tsugu V3.0](https://www.bilibili.com/read/cv18082802/)

## 引用

本插件使用或参考了以下插件/项目

- [NoneBot-Plugin-Alconna](https://github.com/nonebot/plugin-alconna) 提供跨平台以及 Koishi-like 指令支持。
- [nonebot-plugin-userinfo](https://github.com/noneplugin/nonebot-plugin-userinfo) 提供跨平台的用户信息获取支持。
- [tsugu-api-python](https://github.com/WindowsSov8forUs/tsugu-api-python) 提供与 Tsugu 后端的连接支持。
- [tsugu-bangdream-bot](https://github.com/Yamamoto-2/tsugu-bangdream-bot) Tsugu 本体。
