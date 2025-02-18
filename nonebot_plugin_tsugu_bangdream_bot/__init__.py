from typing import TYPE_CHECKING, Any, Set, List, Type, Tuple, Union

from nonebot.log import logger
from nonebot.adapters import Bot, Event, Message
from nonebot.params import RegexGroup, ArgPlainText
from nonebot import on_regex, get_driver, get_plugin_config
from nonebot.plugin import PluginMetadata, require, inherit_supported_adapters

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import Args, Match, Query, Arparma
from nonebot_plugin_alconna.uniseg import At, Reply, UniMessage
from nonebot_plugin_alconna import (
    Field,
    Alconna,
    Command,
    Extension,
    namespace,
    CommandMeta,
    AlconnaMatcher,
    store_true,
    command_manager,
    referent,
    on_alconna,
)

require("nonebot_plugin_userinfo")

from nonebot_plugin_userinfo import get_user_info

from .config import Config
from ._utils import USAGES, server_name_to_id, tier_list_of_server_to_string
from ._commands import (
    room_list,
    song_meta,
    song_chart,
    search_ycx,
    event_stage,
    player_bind,
    player_info,
    random_song,
    search_card,
    search_song,
    forward_room,
    search_event,
    search_gacha,
    search_lsycx,
    player_unbind,
    search_player,
    simulate_gacha,
    switch_forward,
    search_ycx_all,
    _get_tsugu_user,
    get_player_list,
    search_character,
    switch_main_server,
    set_default_servers,
    switch_player_index,
    get_card_illustration,
    server_id_to_full_name,
    server_name_fuzzy_search,
    difficulty_id_fuzzy_search
)

import tsugu_api_async
from tsugu_api_core.exception import FailedException

if TYPE_CHECKING:
    
    from tsugu_api_core._typing import ServerId

_config = get_plugin_config(Config)
_command_start = get_driver().config.command_start

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-tsugu-bangdream-bot",
    description="Koishi-Plugin-Tsugu-BanGDream-Bot 的 NoneBot2 实现",
    usage="\n\n".join([f"{key}: {value}" for key, value in USAGES.items()]),
    type="application",
    homepage="https://github.com/WindowsSov8forUs/nonebot-plugin-tsugu-bangdream-bot",
    config=Config,
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna", "nonebot_plugin_userinfo"
    )
)

try:
    from . import _client
    from tsugu_api_core import register_client
    
    register_client(_client.Client)
except ImportError:
    # 尝试导入两个内置客户端适配的库
    try:
        import httpx
        tsugu_api_async.settings.client = tsugu_api_async.settings.Client.HTTPX
    except ImportError:
        try:
            import aiohttp
            tsugu_api_async.settings.client = tsugu_api_async.settings.Client.AIO_HTTP
        except ImportError:
            raise ImportError("Failed to import httpx and aiohttp, please install one of them to use this plugin.")

tsugu_api_async.settings.use_easy_bg = _config.tsugu_use_easy_bg
tsugu_api_async.settings.compress = _config.tsugu_compress

if len(_config.tsugu_backend_url) > 0:
    tsugu_api_async.settings.backend_url = _config.tsugu_backend_url
if len(_config.tsugu_data_backend_url) > 0:
    tsugu_api_async.settings.userdata_backend_url = _config.tsugu_data_backend_url

tsugu_api_async.settings.proxy = _config.tsugu_proxy
tsugu_api_async.settings.backend_proxy = _config.tsugu_backend_proxy
tsugu_api_async.settings.userdata_backend_proxy = _config.tsugu_data_backend_proxy
tsugu_api_async.settings.timeout = _config.tsugu_timeout

class TsuguExtension(Extension):
    @property
    def priority(self) -> int:
        return 10

    @property
    def id(self) -> str:
        return "TsuguExtension"

    def __init__(self, reply: bool, at: bool) -> None:
        self.reply = reply
        self.at = at

    async def permission_check(self, bot: Bot, event: Event, command: Alconna) -> bool:
        # 规避机器人自身的消息
        try:
            user_id = event.get_user_id()
        except:
            return True
        
        if user_id == bot.self_id:
            return False
        
        return True

    async def send_wrapper(self, bot: Bot, event: Event, send: Union[str, Message, UniMessage]) -> Union[str, Message, UniMessage]:
        if not self.reply and not self.at:
            return send
        if self.at:
            try:
                user_id = event.get_user_id()
                send = At('user', target=user_id) + " " + send
            except:
                pass
        if self.reply:
            try:
                message_id = UniMessage.get_message_id(event, bot)
                send = Reply(message_id) + send
            except:
                pass
        return send

extension = TsuguExtension(_config.tsugu_reply, _config.tsugu_at)
meta = CommandMeta(compact=_config.tsugu_no_space)

def _get_platform(bot: Bot) -> str:
    adapter_name = bot.adapter.get_name().lower()
    if adapter_name.startswith("onebot"):
        return "onebot"
    elif adapter_name == "satori":
        try:
            from nonebot.adapters.satori import Bot as SatoriBot
            if isinstance(bot, SatoriBot):
                return bot.platform
            else:
                return "satori"
        except:
            logger.warning("Got Satori adapter, but failed to get platform")
            return adapter_name
    else:
        return adapter_name

# 自动转发房间号，不作为单独命令算入 namespace
@(car_forwarding := on_regex(r"(^(\d{5,6})(.*)$)")).handle()
async def _(bot: Bot, event: Event, group: Tuple[Any, ...] = RegexGroup()) -> None:
    user_info = await get_user_info(bot, event, event.get_user_id())
    
    try:
        tsugu_user = await _get_tsugu_user(_get_platform(bot), event.get_user_id())
    except Exception as exception:
        logger.warning(f"Failed to get user data: '{exception}'")
        car_forwarding.skip()
    
    if isinstance(tsugu_user, str):
        logger.warning(f"Failed to get user data: '{tsugu_user}'")
        car_forwarding.skip()
    
    try:
        is_forwarded = await forward_room(
            int(group[1]),
            group[0],
            tsugu_user,
            "red",
            user_info.user_id if user_info is not None else event.get_user_id(),
            user_info.user_name if user_info is not None else event.get_user_id(),
            _config.tsugu_bandori_station_token
        )
    except Exception as exception:
        logger.warning(f"Failed to submit room number: '{exception}'")
        car_forwarding.skip()
    
    if is_forwarded:
        logger.debug(f"Submitted room number: '{group[0]}'")

# 统一的命令参数预处理，添加帮助指令自动回复
async def _process_if_unmatch(matcher: AlconnaMatcher, arp: Arparma) -> None:
    if not arp.matched:
        # 指令参数格式不匹配
        error_msg = (
            str(arp.error_info)
            + '\n'
            + matcher.command().get_help()
        )
        await matcher.finish(error_msg)
    else:
        matcher.skip()

# 统一的命令 build 方法
def _build(cmd: Command, aliases: Set[str]) -> Type[AlconnaMatcher]:
    _matcher = cmd.build(
        skip_for_unmatch=False,
        auto_send_output=False,
        aliases=aliases,
        extensions=[extension],
        use_cmd_start=True
    )
    _matcher.handle()(_process_if_unmatch)
    return _matcher

# 定义 tsugu namespace
with namespace("tsugu") as tsugu_namespace:
    
    @(open_forward := _build(Command("开启车牌转发", "开启车牌转发", meta=meta), _config.tsugu_open_forward_aliases)).handle()
    async def _(bot: Bot, event: Event) -> None:
        user_id = event.get_user_id()
        await open_forward.send(await switch_forward(_get_platform(bot), user_id, True))

    @(close_forward := _build(Command("关闭车牌转发", "关闭车牌转发", meta=meta), _config.tsugu_close_forward_aliases)).handle()
    async def _(bot: Bot, event: Event) -> None:
        user_id = event.get_user_id()
        await close_forward.send(await switch_forward(_get_platform(bot), user_id, False))

    @(bind_player := _build(
        Command("绑定玩家 [server_name:str]", "绑定玩家信息", meta=meta)
        .usage(
            '开始玩家数据绑定流程，请不要在"绑定玩家"指令后添加玩家ID。'
            '省略服务器名时，默认为绑定到你当前的主服务器。'
            '请在获得临时验证数字后，将玩家签名改为该数字，并回复你的玩家ID'
        ),
        _config.tsugu_bind_player_aliases
    )).handle()
    async def _(server_name: Match[str], bot: Bot, event: Event) -> None:
        if server_name.available:
            try:
                _server = server_name_to_id(server_name.result)
            except ValueError:
                try:
                    _server = await server_name_fuzzy_search(server_name.result)
                except ValueError:
                    await bind_player.finish("错误: 服务器名未能匹配任何服务器")
        else:
            try:
                tsugu_user = await _get_tsugu_user(_get_platform(bot), event.get_user_id())
            except FailedException as exception:
                return await bind_player.finish(exception.response["data"])
            except Exception as exception:
                return await bind_player.finish(f"错误: {exception}")
            
            _server = tsugu_user["mainServer"]
    
        
        return await player_bind(bind_player, _get_platform(bot), event.get_user_id(), _server)

    @bind_player.got("player_id")
    async def _(bot: Bot, event: Event, player_id: str = ArgPlainText()) -> None:
        if not player_id.isnumeric():
            await bind_player.finish("错误: 无效的玩家id")
        
        server = bind_player.get_path_arg("verify_server", None)
        assert server is not None # 理论上不会被触发

        try:
            response = await tsugu_api_async.bind_player_verification(_get_platform(bot), event.get_user_id(), server, int(player_id), "bind")
        except FailedException as exception:
            return await bind_player.finish(exception.response["data"])

        await bind_player.send(f"绑定 {server_id_to_full_name(server)} 玩家 {player_id} 成功，正在生成玩家状态图片")
        
        message = await search_player(_get_platform(bot), event.get_user_id(), int(player_id), server)
        return await bind_player.finish(message)

    @(unbind_player := _build(
        Command("解除绑定 [server_name:str]", "解除当前服务器的玩家绑定", meta=meta)
        .alias("解绑玩家")
        .usage("解除指定服务器的玩家数据绑定。省略服务器名时，默认为当前的主服务器"),
        _config.tsugu_unbind_player_aliases
    )).handle()
    async def _(server_name: Match[str], bot: Bot, event: Event) -> None:
        if server_name.available:
            try:
                _server = server_name_to_id(server_name.result)
            except ValueError:
                try:
                    _server = await server_name_fuzzy_search(server_name.result)
                except ValueError:
                    await bind_player.finish("错误: 服务器名未能匹配任何服务器")
        else:
            try:
                tsugu_user = await _get_tsugu_user(_get_platform(bot), event.get_user_id())
            except FailedException as exception:
                return await bind_player.finish(exception.response["data"])
            except Exception as exception:
                return await bind_player.finish(f"错误: {exception}")
            
            _server = tsugu_user["mainServer"]
    
        
        return await player_unbind(bind_player, _get_platform(bot), event.get_user_id(), _server)

    @unbind_player.got("_anything")
    async def _(bot: Bot, event: Event) -> None:
        server = unbind_player.get_path_arg("verify_server", None)
        assert server is not None
        
        player_id = unbind_player.get_path_arg("player_id", None)
        assert player_id is not None
        
        try:
            response = await tsugu_api_async.bind_player_verification(_get_platform(bot), event.get_user_id(), server, int(player_id), "unbind")
        except FailedException as exception:
            return await bind_player.finish(exception.response["data"])
        
        await unbind_player.finish(response["data"])

    @(main_server := _build(
        Command("主服务器 <server_name:str>", "设置主服务器", meta=meta)
        .alias("服务器模式").alias("切换服务器")
        .usage("将指定的服务器设置为你的主服务器")
        .example("主服务器 cn : 将国服设置为主服务器").example("日服模式 : 将日服设置为主服务器")
        .shortcut(r"(.+服)模式$", {"args": ["{0}"], "prefix": True}),
        _config.tsugu_main_server_aliases
    )).handle()
    async def _(server_name: Match[str], bot: Bot, event: Event) -> None:
        try:
            _server = server_name_to_id(server_name.result)
        except ValueError:
            try:
                _server = await server_name_fuzzy_search(server_name.result)
            except ValueError:
                await bind_player.finish("错误: 服务器名未能匹配任何服务器")
        await main_server.finish(await switch_main_server(_get_platform(bot), event.get_user_id(), _server))

    @(display_servers := _build(
        Command("设置显示服务器 <server_list:str*>", "设定信息显示中的默认服务器排序", meta=meta)
        .alias("默认服务器").alias("设置默认服务器")
        .usage("使用空格分隔服务器列表")
        .example("设置默认服务器 国服 日服 : 将国服设置为第一服务器，日服设置为第二服务器"),
        aliases=_config.tsugu_default_servers_aliases
    )).handle()
    async def _(server_list: List[str], bot: Bot, event: Event) -> None:
        servers: List['ServerId'] = []
        for _server in server_list:
            try:
                _id = server_name_to_id(_server)
            except ValueError:
                await display_servers.finish("错误: 指定了不存在的服务器")
            if _id in servers:
                await display_servers.finish("错误: 指定了重复的服务器")
            servers.append(_id)
        if len(servers) < 1:
            await display_servers.finish("错误: 请指定至少一个服务器")
        
        await display_servers.finish(await set_default_servers(_get_platform(bot), event.get_user_id(), servers))

    @(player_status := _build(
        Command("玩家状态 [index:int] [server_name:str]", "查询自己的玩家状态", meta=meta)
        .shortcut(r"(.+服)玩家状态$", {"args": ["{0}"], "command": f"{list(_command_start)[0]}玩家状态"}),
        _config.tsugu_player_status_aliases
    )).handle()
    async def _(index: Match[int], server_name: Match[str], bot: Bot, event: Event) -> None:
        if index.available:
            _index = index.result
        else:
            _index = None

        if server_name.available:
            _server_name = server_name.result
        else:
            _server_name = None
        
        await player_status.finish(await player_info(_get_platform(bot), event.get_user_id(), _index, _server_name))

    @(player_list := _build(
        Command("玩家状态列表", "查询目前已经绑定的所有玩家信息")
        .alias("玩家列表").alias("玩家信息列表"),
        _config.tsugu_player_list_aliases
    )).handle()
    async def _(bot: Bot, event: Event) -> None:
        return await player_list.finish(await get_player_list(_get_platform(bot), event.get_user_id()))

    @(switch_index := _build(
        Command("玩家默认ID <index:int>", "设置默认显示的玩家ID")
        .usage(
            "调整玩家状态指令，和发送车牌时的默认玩家信息。\n"
            "规则: \n如果该ID对应的玩家信息在当前默认服务器中, 显示。\n"
            "如果不在当前默认服务器中, 显示当前默认服务器的编号最靠前的玩家信息"
        ).alias("默认玩家ID").alias("默认玩家").alias("玩家ID"),
        _config.tsugu_switch_index_aliases
    )).handle()
    async def _(index: Match[int], bot: Bot, event: Event) -> None:
        return await switch_index.finish(await switch_player_index(_get_platform(bot), event.get_user_id(), index.result))

    @(ycm := _build(
        Command("ycm <keyword:str*>", "获取车牌", meta=meta)
        .alias("有车吗").alias("车来")
        .usage("获取所有车牌车牌，可以通过关键词过滤")
        .example("ycm : 获取所有车牌").example('ycm 大分: 获取所有车牌，其中包含"大分"关键词的车牌'),
        _config.tsugu_ycm_aliases
    )).handle()
    async def _(keyword: List[str]) -> None:
        if len(keyword) > 0:
            _keyword = " ".join(keyword)
        else:
            _keyword = None
        
        await ycm.finish(await room_list(_keyword))

    @(player_search := _build(
        Command("查玩家 <player_id:int> [server_name:str]", "查询玩家信息", meta=meta)
        .alias("查询玩家")
        .usage("查询指定ID玩家的信息。省略服务器名时，默认从你当前的主服务器查询")
        .example("查玩家 10000000 : 查询你当前默认服务器中，玩家ID为10000000的玩家信息").example("查玩家 40474621 jp : 查询日服玩家ID为40474621的玩家信息"),
        aliases=_config.tsugu_search_player_aliases
    )).handle()
    async def _(player_id: Match[int], server_name: Match[str], bot: Bot, event: Event) -> None:
        if not player_id.available:
            await player_search.finish("错误: 未指定玩家ID")
        
        if server_name.available:
            try:
                _server = server_name_to_id(server_name.result)
            except ValueError:
                await player_search.finish("错误: 服务器名未能匹配任何服务器")
        else:
            _server = None

        await player_search.finish(await search_player(_get_platform(bot), event.get_user_id(), player_id.result, _server))

    @(card_search := _build(
        Command("查卡 <word:str*>", "查卡", meta=meta).alias("查卡牌")
        .usage("根据关键词或卡牌ID查询卡片信息，请使用空格隔开所有参数")
        .example("查卡 1399 :返回1399号卡牌的信息").example("查卡 绿 tsugu :返回所有属性为pure的羽泽鸫的卡牌列表"),
        _config.tsugu_search_card_aliases
    )).handle()
    async def _(word: List[str], bot: Bot, event: Event) -> None:
        await card_search.finish(await search_card(_get_platform(bot), event.get_user_id(), " ".join(word)))

    @(card_illustration := _build(
        Command("查卡面 <card_id:int>", "查卡面", meta=meta)
        .alias("查卡插画").alias("查插画")
        .usage("根据卡片ID查询卡片插画")
        .example("查卡面 1399 :返回1399号卡牌的插画"),
        _config.tsugu_card_illustration_aliases
    )).handle()
    async def _(card_id: Match[int]) -> None:
        await card_illustration.finish(await get_card_illustration(card_id.result))

    @(character_search := _build(
        Command("查角色 <word:str*>", "查角色", meta=meta)
        .usage("根据关键词或角色ID查询角色信息")
        .example("查角色 10 :返回10号角色的信息").example("查角色 吉他 :返回所有角色模糊搜索标签中包含吉他的角色列表"),
        _config.tsugu_search_character_aliases
    )).handle()
    async def _(word: List[str], bot: Bot, event: Event) -> None:
        await character_search.finish(await search_character(_get_platform(bot), event.get_user_id(), " ".join(word)))

    @(event_search := _build(
        Command("查活动 <word:str*>", "查活动", meta=meta)
        .usage("根据关键词或活动ID查询活动信息")
        .example("查活动 177 :返回177号活动的信息").example("查活动 绿 tsugu :返回所有属性加成为pure，且活动加成角色中包括羽泽鸫的活动列表"),
        _config.tsugu_search_event_aliases
    )).handle()
    async def _(word: List[str], bot: Bot, event: Event) -> None:
        await event_search.finish(await search_event(_get_platform(bot), event.get_user_id(), " ".join(word)))

    @(song_search := _build(
        Command("查曲 <word:str*>", "查曲", meta=meta)
        .usage("根据关键词或曲目ID查询曲目信息")
        .example("查曲 1 :返回1号曲的信息").example("查曲 ag lv27 :返回所有难度为27的ag曲列表"),
        _config.tsugu_search_song_aliases
    )).handle()
    async def _(word: List[str], bot: Bot, event: Event) -> None:
        await song_search.finish(await search_song(_get_platform(bot), event.get_user_id(), " ".join(word)))

    @(chart_search := _build(
        Command("查谱面 <song_id:int> [difficulty:str]", "查谱面", meta=meta)
        .usage("根据曲目ID与难度查询谱面信息")
        .example("查谱面 1 :返回1号曲的所有谱面").example("查谱面 1 expert :返回1号曲的expert难度谱面"),
        _config.tsugu_song_chart_aliases
    )).handle()
    async def _(song_id: Match[int], bot: Bot, event: Event, difficulty: str = "expert") -> None:
        try:
            difficulty_id = await difficulty_id_fuzzy_search(difficulty)
        except ValueError:
            await chart_search.finish("错误: 难度名未能匹配任何难度")
        
        await chart_search.finish(await song_chart(_get_platform(bot), event.get_user_id(), song_id.result, difficulty_id))

    @(song_random := _build(
        Command("随机曲 <word:str*>", "随机曲", meta=meta)
        .alias("随机")
        .example("随机曲 lv24 :在所有包含24等级难度的曲中, 随机返回其中一个").example("随机曲 lv24 ag :在所有包含24等级难度的afterglow曲中, 随机返回其中一个"),
        _config.tsugu_song_random_aliases
    )).handle()
    async def _(word: List[str], bot: Bot, event: Event) -> None:
        await song_random.finish(await random_song(_get_platform(bot), event.get_user_id(), " ".join(word)))

    @(meta_search := _build(
        Command("查询分数表 <server_name:str>", "查询分数表", meta=meta)
        .usage("查询指定服务器的歌曲分数表，如果没有服务器名的话，服务器为用户的默认服务器")
        .alias("查分数表").alias("查询分数榜").alias("查分数榜")
        .example("查询分数表 cn :返回国服的歌曲分数表"),
        _config.tsugu_song_meta_aliases
    )).handle()
    async def _(server_name: Match[str], bot: Bot, event: Event) -> None:
        try:
            _server = server_name_to_id(server_name.result)
        except ValueError:
            try:
                _server = await server_name_fuzzy_search(server_name.result)
            except ValueError:
                await meta_search.finish("错误: 服务器名未能匹配任何服务器")
        
        await meta_search.finish(await song_meta(_get_platform(bot), event.get_user_id(), _server))

    @(stage_search := _build(
        Command("查试炼 [event_id:int]", "查试炼", meta=meta)
        .usage("查询当前服务器当前活动试炼信息\n可以自定义活动ID\n参数:-m 显示歌曲meta(相对效率)")
        .alias("查stage").alias("查舞台").alias("查festival").alias("查5v5")
        .example("查试炼 157 -m :返回157号活动的试炼信息，包含歌曲meta")
        .example("查试炼 -m :返回当前活动的试炼信息，包含歌曲meta").example("查试炼 :返回当前活动的试炼信息")
        .option("meta", "-m", False, store_true),
        _config.tsugu_event_stage_aliases
    )).handle()
    async def _(event_id: Match[int], bot: Bot, event: Event, meta: Query[bool]=Query("meta.value", False)) -> None:
        if event_id.available:
            _event_id = event_id.result
        else:
            _event_id = None
        
        await stage_search.finish(await event_stage(_get_platform(bot), event.get_user_id(), _event_id, meta.result))

    @(gacha_search := _build(
        Command("查卡池 <gacha_id:int>", "查卡池", meta=meta)
        .usage("根据卡池ID查询卡池信息"),
        _config.tsugu_search_gacha_aliases
    )).handle()
    async def _(gacha_id: Match[int], bot: Bot, event: Event) -> None:
        await gacha_search.finish(await search_gacha(_get_platform(bot), event.get_user_id(), gacha_id.result))

    @(ycx := _build(
        Command("ycx <tier:int> [event_id:int] [server_name:str]", "查询指定档位的预测线", meta=meta)
        .usage(
            f"查询指定档位的预测线，如果没有服务器名的话，服务器为用户的默认服务器。"
            "如果没有活动ID的话，活动为当前活动\n可用档线:\n{tier_list_of_server_to_string()}"
        ).example("ycx 1000 :返回默认服务器当前活动1000档位的档线与预测线").example("ycx 1000 177 jp:返回日服177号活动1000档位的档线与预测线"),
        _config.tsugu_ycx_aliases
    )).handle()
    async def _(tier: Match[int], event_id: Match[int], server_name: Match[str], bot: Bot, event: Event) -> None:
        if event_id.available:
            _event_id = event_id.result
        else:
            _event_id = None
        
        if server_name.available:
            try:
                _server = server_name_to_id(server_name.result)
            except ValueError:
                try:
                    _server = await server_name_fuzzy_search(server_name.result)
                except ValueError:
                    await ycx.finish("错误: 服务器名未能匹配任何服务器")
        else:
            _server = None
        
        await ycx.finish(await search_ycx(_get_platform(bot), event.get_user_id(), tier.result, _event_id, _server))

    @(ycx_all := _build(
        Command("ycxall [event_id:int] [server_name:str]", "查询所有档位的预测线", meta=meta)
        .usage(
            f"查询所有档位的预测线，如果没有服务器名的话，服务器为用户的默认服务器。"
            "如果没有活动ID的话，活动为当前活动\n可用档线:\n{tier_list_of_server_to_string()}"
        ).alias("myycx"),
        _config.tsugu_ycx_all_aliases
    )).handle()
    async def _(event_id: Match[int], server_name: Match[str], bot: Bot, event: Event) -> None:
        if event_id.available:
            _event_id = event_id.result
        else:
            _event_id = None
        
        if server_name.available:
            try:
                _server = server_name_to_id(server_name.result)
            except ValueError:
                try:
                    _server = await server_name_fuzzy_search(server_name.result)
                except ValueError:
                    await ycx_all.finish("错误: 服务器名未能匹配任何服务器")
        else:
            _server = None
        
        await ycx_all.finish(await search_ycx_all(_get_platform(bot), event.get_user_id(), _server, _event_id))

    @(lsycx := _build(
        Command("lsycx <tier:int> [event_id:int] [server_name:str]", "查询指定档位的预测线", meta=meta)
        .usage(
            "查询指定档位的预测线，与最近的4期活动类型相同的活动的档线数据，如果没有服务器名的话，服务器为用户的默认服务器。"
            + f"如果没有活动ID的话，活动为当前活动\n可用档线:\n{tier_list_of_server_to_string()}"
        ).example("lsycx 1000 :返回默认服务器当前活动的档线与预测线，与最近的4期活动类型相同的活动的档线数据").example("lsycx 1000 177 jp:返回日服177号活动1000档位档线与最近的4期活动类型相同的活动的档线数据"),
        _config.tsugu_lsycx_aliases
    )).handle()
    async def _(tier: Match[int], event_id: Match[int], server_name: Match[str], bot: Bot, event: Event) -> None:
        if event_id.available:
            _event_id = event_id.result
        else:
            _event_id = None
        
        if server_name.available:
            try:
                _server = server_name_to_id(server_name.result)
            except ValueError:
                try:
                    _server = await server_name_fuzzy_search(server_name.result)
                except ValueError:
                    await lsycx.finish("错误: 服务器名未能匹配任何服务器")
        else:
            _server = None
        
        await lsycx.finish(await search_lsycx(_get_platform(bot), event.get_user_id(), tier.result, _event_id, _server))

    @(gacha_simulate := _build(
        Command("抽卡模拟 [times:int] [gacha_id:int]", meta=meta)
        .usage("模拟抽卡，如果没有卡池ID的话，卡池为当前活动的卡池")
        .example("抽卡模拟:模拟抽卡10次").example("抽卡模拟 300 922 :模拟抽卡300次，卡池为922号卡池"),
        _config.tsugu_gacha_simulate_aliases
    )).handle()
    async def _(times: Match[int], gacha_id: Match[int], bot: Bot, event: Event) -> None:
        if times.available:
            _times = times.result
        else:
            _times = None
        
        if gacha_id.available:
            _gacha_id = gacha_id.result
        else:
            _gacha_id = None
        
        await gacha_simulate.finish(await simulate_gacha(_get_platform(bot), event.get_user_id(), _times, _gacha_id))

# help 的内部实现，避免对其他 help 产生阻塞
@(_help := on_alconna(
    Alconna("help", Args["query#输入命令名称查看帮助;/?", str, Field("-1")], meta=CommandMeta(description="显示命令帮助")),
    use_cmd_start=True,
    auto_send_output=True
)).handle()
async def _(arp: Arparma) -> None:
    cmds = [i for i in command_manager.get_commands("tsugu") if not i.meta.hide]
    if (query := arp.all_matched_args["query"]) != "-1":
        for index, slot in enumerate(cmds):
            if query == slot.command or query in list(command_manager.get_shortcut(slot).keys()):
                break
        else:
            return await _help.skip()
        slot = cmds[index]
        try:
            _matcher = referent(slot)
            assert _matcher is not None
            executor = _matcher.executor
            msg = await executor.output_converter("help", slot.get_help())
            msg = msg or slot.get_help()
        except Exception:
            msg = slot.get_help()
        return await _help.finish(msg)
    else:
        return await _help.skip()
