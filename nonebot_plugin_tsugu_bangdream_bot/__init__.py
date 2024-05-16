from typing import Any, List, Tuple, Union, Optional

from nonebot.log import logger
from nonebot.adapters import Bot, Event, Message
from nonebot.plugin import PluginMetadata, require
from nonebot.params import RegexGroup, ArgPlainText
from nonebot import on_regex, get_driver, get_plugin_config

require("nonebot_plugin_alconna")

from nonebot.typing import T_State
from nonebot_plugin_alconna import load_builtin_plugin
from nonebot_plugin_alconna import Command, Arparma, Extension, store_true
from nonebot_plugin_alconna.uniseg import At, Text, Image, Reply, Segment, UniMessage

require("nonebot_plugin_userinfo")

from nonebot_plugin_userinfo import get_user_info

load_builtin_plugin("help")

from .config import Config
from ._utils import USAGES, COMMAND_KEYWORDS, server_name_to_id, tier_list_of_server_to_string
from ._commands import (
    room_list,
    song_meta,
    song_chart,
    search_ycx,
    event_stage,
    player_bind,
    player_info,
    search_card,
    search_song,
    search_event,
    search_gacha,
    search_lsycx,
    player_unbind,
    search_player,
    simulate_gacha,
    switch_forward,
    search_ycx_all,
    search_character,
    switch_main_server,
    set_default_servers,
    get_card_illustration
)

import tsugu_api_async
from tsugu_api_async._typing import _ServerId

class NoSpaceExtension(Extension):
    @property
    def priority(self) -> int:
        return 10
    
    @property
    def id(self) -> str:
        return "TsuguNoSpaceExtension"
    
    def __init__(self, reply: bool, at: bool, no_space: bool) -> None:
        self.reply = reply
        self.at = at
        self.no_space = no_space
    
    async def message_provider(self, event: Event, state: T_State, bot: Bot, use_origin: bool = False) -> Optional[Union[Message, UniMessage]]:
        msg = await super().message_provider(event, state, bot, use_origin)
        
        if msg is None:
            return None
        
        if self.no_space:
            msg = msg.extract_plain_text().strip()
            for keyword in COMMAND_KEYWORDS:
                if msg.startswith(keyword) and not msg.startswith(keyword + " "):
                    msg = msg.replace(keyword, keyword + " ", 1)
            
            return UniMessage(msg)
        else:
            return msg
    
    async def send_wrapper(self, bot: Bot, event: Event, send: Union[str, Message, UniMessage]) -> Union[str, Message, UniMessage]:
        if not self.reply and not self.at:
            return send
        if self.at:
            try:
                user_id = event.get_user_id()
                send = At('user', target=user_id) + send
            except:
                pass
        if self.reply:
            try:
                message_id = UniMessage.get_message_id(event, bot)
                send = Reply(message_id) + send
            except:
                pass
        return send

config = get_plugin_config(Config)

if "httpx" in get_driver().type:
    tsugu_api_async.settings.client = tsugu_api_async.settings.Client.HTTPX
elif "aiohttp" in get_driver().type:
    tsugu_api_async.settings.client = tsugu_api_async.settings.Client.AIO_HTTP

tsugu_api_async.settings.use_easy_bg = config.tsugu_use_easy_bg
tsugu_api_async.settings.compress = config.tsugu_compress

if len(config.tsugu_backend_url) > 0:
    tsugu_api_async.settings.backend_url = config.tsugu_backend_url
if len(config.tsugu_data_backend_url) > 0:
    tsugu_api_async.settings.userdata_backend_url = config.tsugu_data_backend_url

tsugu_api_async.settings.proxy = config.tsugu_proxy
tsugu_api_async.settings.backend_proxy = config.tsugu_backend_proxy
tsugu_api_async.settings.userdata_backend_proxy = config.tsugu_data_backend_proxy

extension = NoSpaceExtension(config.tsugu_reply, config.tsugu_at, config.tsugu_no_space)

car_forwarding = on_regex(r"(^(\d{5,6})(.*)$)")

@car_forwarding.handle()
async def _(bot: Bot, event: Event, group: Tuple[Any, ...] = RegexGroup()) -> None:
    user_info = await get_user_info(bot, event, event.get_user_id())
    try:
        response = await tsugu_api_async.station_submit_room_number(
            int(group[1]),
            group[0],
            "red",
            user_info.user_id,
            user_info.user_name,
            config.tsugu_bandori_station_token
        )
    except Exception as exception:
        logger.error(f"Failed to submit room number: {exception}")
        await car_forwarding.finish()
    
    if response["status"] == "failed":
        logger.warning(f"Failed to submit room number: {response['data']}")
        await car_forwarding.finish()

open_forward = Command("开启车牌转发", "开启车牌转发").build(aliases=config.tsugu_open_forward_aliases, extensions=[extension])

@open_forward.handle()
async def _(event: Event) -> None:
    user_id = event.get_user_id()
    await open_forward.send(await switch_forward(user_id, True))

close_forward = Command("关闭车牌转发", "关闭车牌转发").build(aliases=config.tsugu_close_forward_aliases, extensions=[extension])

@close_forward.handle()
async def _(event: Event) -> None:
    user_id = event.get_user_id()
    await close_forward.send(await switch_forward(user_id, False))

bind_player = (
    Command("绑定玩家 [server_name:str]", "绑定玩家信息")
    .usage('开始玩家数据绑定流程，请不要在"绑定玩家"指令后添加玩家ID。省略服务器名时，默认为绑定到你当前的主服务器。请在获得临时验证数字后，将玩家签名改为该数字，并回复你的玩家ID')
    .build(aliases=config.tsugu_bind_player_aliases, extensions=[extension])
)

@bind_player.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("server_name"):
        server = arp.query[str]("server_name")
        if server is None:
            _server = None
        else:
            try:
                _server = server_name_to_id(server)
            except ValueError:
                await bind_player.finish("错误: 服务器不存在，请不要在参数中添加玩家ID")
    else:
        _server = None
    
    reply, available, server = await player_bind(event.get_user_id(), _server)
    
    if not available:
        await bind_player.finish(reply)
    else:
        bind_player.set_path_arg("verify_server", server)
        await bind_player.send(reply)

@bind_player.got("player_id")
async def _(event: Event, player_id: str = ArgPlainText()) -> None:
    if not player_id.isnumeric():
        await bind_player.finish("错误: 无效的玩家id")
    
    server = bind_player.get_path_arg("verify_server", None)
    assert server is not None
    
    response = await tsugu_api_async.bind_player_verification("red", event.get_user_id(), server, int(player_id), True)
    
    await bind_player.finish(response["data"])

unbind_player = (
    Command("解除绑定 [server_name:str]", "解除当前服务器的玩家绑定").alias("解绑玩家")
    .usage("解除指定服务器的玩家数据绑定。省略服务器名时，默认为当前的主服务器")
    .build(aliases=config.tsugu_unbind_player_aliases, extensions=[extension])
)

@unbind_player.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("server_name"):
        server = arp.query[str]("server_name")
        if server is None:
            _server = None
        else:
            try:
                _server = server_name_to_id(server)
            except ValueError:
                await unbind_player.finish("错误: 服务器不存在，请不要在参数中添加玩家ID")
    else:
        _server = None
    
    reply, available, server, player_id = await player_unbind(event.get_user_id(), _server)
    
    if not available:
        await unbind_player.finish(reply)
    else:
        unbind_player.set_path_arg("verify_server", server)
        unbind_player.set_path_arg("player_id", player_id)
        await unbind_player.send(reply)

@unbind_player.got("_anything")
async def _(event: Event) -> None:
    server = unbind_player.get_path_arg("verify_server", None)
    assert server is not None
    
    player_id = unbind_player.get_path_arg("player_id", None)
    assert player_id is not None
    
    response = await tsugu_api_async.bind_player_verification("red", event.get_user_id(), server, int(player_id), False)
    
    await unbind_player.finish(response["data"])

main_server = (
    Command("主服务器 <server_name:str>", "设置主服务器")
    .alias("服务器模式").alias("切换服务器")
    .usage("将指定的服务器设置为你的主服务器")
    .example("主服务器 cn : 将国服设置为主服务器")
    .example("日服模式 : 将日服设置为主服务器")
    .shortcut(r"^(.+服)模式$", {"args": ["{0}"]})
    .build(aliases=config.tsugu_main_server_aliases, extensions=[extension])
)

@main_server.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("server_name"):
        server = arp.query[str]("server_name")
        if server is None:
            await main_server.finish("错误: 未指定服务器")
        try:
            _server = server_name_to_id(server)
        except ValueError:
            await main_server.finish("错误: 服务器不存在")
        await main_server.finish(await switch_main_server(event.get_user_id(), _server))
    else:
        await main_server.finish("错误: 未指定服务器")

default_servers = (
    Command("设置默认服务器 <server_list:str+:>", "设定信息显示中的默认服务器排序")
    .alias("默认服务器")
    .usage("使用空格分隔服务器列表")
    .example("设置默认服务器 国服 日服 : 将国服设置为第一服务器，日服设置为第二服务器")
    .build(aliases=config.tsugu_default_servers_aliases, extensions=[extension])
)

@default_servers.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("server_list"):
        server_list = arp.query[List[str]]("server_list")
        if server_list is None:
            await default_servers.finish("错误: 请指定至少一个服务器")
        servers: List[_ServerId] = []
        for _server in server_list:
            try:
                _id = server_name_to_id(_server)
            except ValueError:
                await default_servers.finish("错误: 指定了不存在的服务器")
            if _id in servers:
                await default_servers.finish("错误: 指定了重复的服务器")
            servers.append(_id)
        if len(servers) < 1:
            await default_servers.finish("错误: 请指定至少一个服务器")
        
        await default_servers.finish(await set_default_servers(event.get_user_id(), servers))
    else:
        await default_servers.finish("错误: 请指定至少一个服务器")

player_status = (
    Command("玩家状态 [server_name:str]", "查询自己的玩家状态")
    .shortcut(r"^(.+服)玩家状态$", {"args": ["{0}"]})
    .build(aliases=config.tsugu_player_status_aliases, extensions=[extension])
)

@player_status.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("server_name"):
        server = arp.query[str]("server_name")
        if server is None:
            _server = None
        else:
            try:
                _server = server_name_to_id(server)
            except ValueError:
                await player_status.finish("错误: 服务器不存在")
    else:
        _server = None
    
    result = await player_info(event.get_user_id(), _server)
    segments: List[Segment] = []
    for _r in result:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await player_status.finish(UniMessage(segments))

ycm = (
    Command("ycm [keyword:str+:]", "获取车牌")
    .alias("有车吗").alias("车来")
    .usage("获取所有车牌车牌，可以通过关键词过滤")
    .example("ycm : 获取所有车牌").example('ycm 大分: 获取所有车牌，其中包含"大分"关键词的车牌')
    .build(aliases=config.tsugu_ycm_aliases, extensions=[extension])
)

@ycm.handle()
async def _(arp: Arparma) -> None:
    if arp.find("keyword"):
        keywords = arp.query[List[str]]("keyword", [])
        keyword = " ".join(keywords)
    else:
        keyword = None
    
    try:
        response = await room_list(keyword)
    except Exception as exception:
        await ycm.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await ycm.finish(UniMessage(segments))

player_search = (
    Command("查玩家 <player_id:int> [server_name:str]", "查询玩家信息")
    .alias("查询玩家")
    .usage("查询指定ID玩家的信息。省略服务器名时，默认从你当前的主服务器查询")
    .example("查玩家 10000000 : 查询你当前默认服务器中，玩家ID为10000000的玩家信息")
    .example("查玩家 40474621 jp : 查询日服玩家ID为40474621的玩家信息")
    .build(aliases=config.tsugu_search_player_aliases, extensions=[extension])
)

@player_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("player_id"):
        player_id = arp.query[int]("player_id")
    else:
        await player_search.finish("错误: 未指定玩家ID")
    
    assert player_id is not None
    
    if arp.find("server_name"):
        server = arp.query[str]("server_name")
        if server is None:
            _server = None
        else:
            try:
                _server = server_name_to_id(server)
            except ValueError:
                await player_search.finish("错误: 服务器不存在")
    else:
        _server = None
    
    if _server is None:
        try:
            _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
        except Exception as exception:
            await player_search.finish(f"错误: {exception}")
        
        if _response["status"] == "failed":
            assert isinstance(_response["data"], str)
            await player_search.finish(_response["data"])
        
        assert isinstance(_response["data"], dict)
        tsugu_user = _response["data"]
        _server = tsugu_user["server_mode"]
    
    result = await search_player(player_id, _server)
    segments: List[Segment] = []
    for _r in result:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await player_search.finish(UniMessage(segments))

card_search = (
    Command("查卡 <word:str+:>", "查卡").alias("查卡牌")
    .usage("根据关键词或卡牌ID查询卡片信息，请使用空格隔开所有参数")
    .example("查卡 1399 :返回1399号卡牌的信息")
    .example("查卡 绿 tsugu :返回所有属性为pure的羽泽鸫的卡牌列表")
    .build(aliases=config.tsugu_search_card_aliases, extensions=[extension])
)

@card_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("word"):
        words = arp.query[str]("word", [])
        word = " ".join(words)
    else:
        word = ""
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _servers = tsugu_user["default_server"]

    try:
        response = await search_card(word, _servers)
    except Exception as exception:
        await card_search.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await card_search.finish(UniMessage(segments))

card_illustration = (
    Command("查卡面 <card_id:int>", "查卡面").alias("查卡插画").alias("查插画")
    .usage("根据卡片ID查询卡片插画").example("查卡面 1399 :返回1399号卡牌的插画")
    .build(aliases=config.tsugu_card_illustration_aliases, extensions=[extension])
)

@card_illustration.handle()
async def _(arp: Arparma) -> None:
    if arp.find("card_id"):
        card_id = arp.query[int]("card_id")
    else:
        card_id = None
    
    if card_id is None:
        await card_illustration.finish("错误: 参数错误")
    
    try:
        response = await get_card_illustration(card_id)
    except Exception as exception:
        await card_illustration.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await card_illustration.finish(UniMessage(segments))

character_search = (
    Command("查角色 <word:str+>", "查角色").usage("根据关键词或角色ID查询角色信息")
    .example("查角色 10 :返回10号角色的信息").example("查角色 吉他 :返回所有角色模糊搜索标签中包含吉他的角色列表")
    .build(aliases=config.tsugu_search_character_aliases, extensions=[extension])
)

@character_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("word"):
        words = arp.query[List[str]]("word", [])
        word = " ".join(words)
    else:
        word = ""
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _servers = tsugu_user["default_server"]

    try:
        response = await search_character(word, _servers)
    except Exception as exception:
        await character_search.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await character_search.finish(UniMessage(segments))

event_search = (
    Command("查活动 <word:str+>", "查活动").usage("根据关键词或活动ID查询活动信息")
    .example("查活动 177 :返回177号活动的信息").example("查活动 绿 tsugu :返回所有属性加成为pure，且活动加成角色中包括羽泽鸫的活动列表")
    .build(aliases=config.tsugu_search_event_aliases, extensions=[extension])
)

@event_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("word"):
        words = arp.query[List[str]]("word", [])
        word = " ".join(words)
    else:
        word = ""
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _servers = tsugu_user["default_server"]

    try:
        response = await search_event(word, _servers)
    except Exception as exception:
        await event_search.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await event_search.finish(UniMessage(segments))

song_search = (
    Command("查曲 <word:str+>", "查曲").usage("根据关键词或曲目ID查询曲目信息")
    .example("查曲 1 :返回1号曲的信息").example("查曲 ag lv27 :返回所有难度为27的ag曲列表")
    .build(aliases=config.tsugu_search_song_aliases, extensions=[extension])
)

@song_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("word"):
        words = arp.query[List[str]]("word", [])
        word = " ".join(words)
    else:
        word = ""
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _servers = tsugu_user["default_server"]

    try:
        response = await search_song(word, _servers)
    except Exception as exception:
        await song_search.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await song_search.finish(UniMessage(segments))

chart_search = (
    Command("查谱面 <song_id:int> [difficulty:str]", "查谱面").usage("根据曲目ID与难度查询谱面信息")
    .example("查谱面 1 :返回1号曲的所有谱面").example("查谱面 1 expert :返回1号曲的expert难度谱面")
    .build(aliases=config.tsugu_song_chart_aliases, extensions=[extension])
)

@chart_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("song_id"):
        song_id = arp.query[int]("song_id")
    else:
        song_id = None
    
    if arp.find("difficulty"):
        difficulty = arp.query[str]("difficulty", "expert")
    else:
        difficulty = "expert"
    
    if song_id is None:
        await chart_search.finish("错误: 未指定曲目ID")
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _servers = tsugu_user["default_server"]

    try:
        response = await song_chart(_servers, song_id, difficulty) # type: ignore
    except Exception as exception:
        await chart_search.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await chart_search.finish(UniMessage(segments))

meta_search = (
    Command("查询分数表 <word:str+>", "查询分数表").usage("查询指定服务器的歌曲分数表，如果没有服务器名的话，服务器为用户的默认服务器")
    .alias("查分数表").alias("查询分数榜").alias("查分数榜")
    .example("查询分数表 cn :返回国服的歌曲分数表")
    .build(aliases=config.tsugu_song_meta_aliases, extensions=[extension])
)

@meta_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("word"):
        words = arp.query[List[str]]("word", [])
        word = " ".join(words)
    else:
        word = ""
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    try:
        _server = server_name_to_id(word)
    except ValueError:
        await meta_search.finish("错误: 服务器不存在")
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _servers = tsugu_user["default_server"]

    try:
        response = await song_meta(_servers, _server)
    except Exception as exception:
        await meta_search.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await meta_search.finish(UniMessage(segments))

stage_search = (
    Command("查试炼 [event_id:int]", "查试炼").usage("查询当前服务器当前活动试炼信息\n可以自定义活动ID\n参数:-m 显示歌曲meta(相对效率)")
    .alias("查stage").alias("查舞台").alias("查festival").alias("查5v5")
    .example("查试炼 157 -m :返回157号活动的试炼信息，包含歌曲meta")
    .example("查试炼 -m :返回当前活动的试炼信息，包含歌曲meta")
    .example("查试炼 :返回当前活动的试炼信息")
    .option("meta", "-m", False, store_true)
    .build(aliases=config.tsugu_event_stage_aliases, extensions=[extension])
)

@stage_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("event_id"):
        event_id = arp.query[int]("event_id")
    else:
        event_id = None
    
    if (option := arp.options.get("meta", None)) is None:
        meta = False
    else:
        meta = option.value
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _server = tsugu_user["server_mode"]

    try:
        response = await event_stage(_server, event_id, meta)
    except Exception as exception:
        await stage_search.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await stage_search.finish(UniMessage(segments))

gacha_search = (
    Command("查卡池 <gacha_id:int>", "查卡池").usage("根据卡池ID查询卡池信息")
    .build(aliases=config.tsugu_search_gacha_aliases, extensions=[extension])
)

@gacha_search.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("gacha_id"):
        gacha_id = arp.query[int]("gacha_id")
    else:
        gacha_id = None
    
    if gacha_id is None:
        await gacha_search.finish("错误: 未指定卡池ID")
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _servers = tsugu_user["default_server"]

    try:
        response = await search_gacha(_servers, gacha_id)
    except Exception as exception:
        await gacha_search.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await gacha_search.finish(UniMessage(segments))

ycx = (
    Command("ycx <tier:int> [event_id:int] [server_name:str]", "查询指定档位的预测线")
    .usage(f"查询指定档位的预测线，如果没有服务器名的话，服务器为用户的默认服务器。如果没有活动ID的话，活动为当前活动\n可用档线:\n{tier_list_of_server_to_string()}")
    .example("ycx 1000 :返回默认服务器当前活动1000档位的档线与预测线")
    .example("ycx 1000 177 jp:返回日服177号活动1000档位的档线与预测线")
    .build(aliases=config.tsugu_ycx_aliases, extensions=[extension])
)

@ycx.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("tier"):
        tier = arp.query[int]("tier")
    else:
        tier = None
    
    if tier is None:
        await ycx.finish("请输入排名")
    
    if arp.find("event_id"):
        event_id = arp.query[int]("event_id")
    else:
        event_id = None
    
    if arp.find("server_name"):
        server = arp.query[str]("server_name")
        if server is None:
            _server = None
        else:
            try:
                _server = server_name_to_id(server)
            except ValueError:
                await ycx.finish("错误: 服务器不存在")
    else:
        _server = None
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _server = tsugu_user["server_mode"]

    try:
        response = await search_ycx(_server, tier, event_id)
    except Exception as exception:
        await ycx.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await ycx.finish(UniMessage(segments))

ycx_all = (
    Command("ycxall [event_id:int] [server_name:str]", "查询所有档位的预测线")
    .usage(f"查询所有档位的预测线，如果没有服务器名的话，服务器为用户的默认服务器。如果没有活动ID的话，活动为当前活动\n可用档线:\n{tier_list_of_server_to_string()}")
    .alias("myycx")
    .build(aliases=config.tsugu_ycx_all_aliases, extensions=[extension])
)

@ycx_all.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("event_id"):
        event_id = arp.query[int]("event_id")
    else:
        event_id = None
    
    if arp.find("server_name"):
        server = arp.query[str]("server_name")
        if server is None:
            _server = None
        else:
            try:
                _server = server_name_to_id(server)
            except ValueError:
                await ycx_all.finish("错误: 服务器不存在")
    else:
        _server = None
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _server = tsugu_user["server_mode"]

    try:
        response = await search_ycx_all(_server, event_id)
    except Exception as exception:
        await ycx_all.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await ycx_all.finish(UniMessage(segments))

lsycx = (
    Command("lsycx <tier:int> [event_id:int] [server_name:str]", "查询指定档位的预测线")
    .usage(f"查询指定档位的预测线，与最近的4期活动类型相同的活动的档线数据，如果没有服务器名的话，服务器为用户的默认服务器。如果没有活动ID的话，活动为当前活动\n可用档线:\n{tier_list_of_server_to_string()}")
    .example("lsycx 1000 :返回默认服务器当前活动的档线与预测线，与最近的4期活动类型相同的活动的档线数据")
    .example("lsycx 1000 177 jp:返回日服177号活动1000档位档线与最近的4期活动类型相同的活动的档线数据")
    .build(aliases=config.tsugu_lsycx_aliases, extensions=[extension])
)

@lsycx.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("tier"):
        tier = arp.query[int]("tier")
    else:
        tier = None
    
    if tier is None:
        await lsycx.finish("请输入排名")
    
    if arp.find("event_id"):
        event_id = arp.query[int]("event_id")
    else:
        event_id = None
    
    if arp.find("server_name"):
        server = arp.query[str]("server_name")
        if server is None:
            _server = None
        else:
            try:
                _server = server_name_to_id(server)
            except ValueError:
                await lsycx.finish("错误: 服务器不存在")
    else:
        _server = None
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _server = tsugu_user["server_mode"]

    try:
        response = await search_lsycx(_server, tier, event_id)
    except Exception as exception:
        await lsycx.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await lsycx.finish(UniMessage(segments))

gacha_simulate = (
    Command("抽卡模拟 [times:int] [gacha_id:int]").usage("模拟抽卡，如果没有卡池ID的话，卡池为当前活动的卡池")
    .example("抽卡模拟:模拟抽卡10次").example("抽卡模拟 300 922 :模拟抽卡300次，卡池为922号卡池")
    .build(aliases=config.tsugu_gacha_simulate_aliases, extensions=[extension])
)

@gacha_simulate.handle()
async def _(arp: Arparma, event: Event) -> None:
    if arp.find("times"):
        times = arp.query[int]("times")
    else:
        times = None
    
    if arp.find("gacha_id"):
        gacha_id = arp.query[int]("gacha_id")
    else:
        gacha_id = None
    
    try:
        _response = await tsugu_api_async.get_user_data("red", event.get_user_id())
    except Exception as exception:
        await player_search.finish(f"错误: {exception}")
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        await player_search.finish(_response["data"])
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    _server = tsugu_user["server_mode"]

    try:
        response = await simulate_gacha(_server, times, gacha_id)
    except Exception as exception:
        await gacha_simulate.finish(f"错误: {exception}")
    
    segments: List[Segment] = []
    for _r in response:
        if isinstance(_r, str):
            segments.append(Text(_r))
        else:
            segments.append(Image(raw=_r))
    
    await gacha_simulate.finish(UniMessage(segments))

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-tsugu-bangdream-bot",
    description="Koishi-Plugin-Tsugu-BanGDream-Bot 的 NoneBot2 实现",
    usage="\n".join([f"{key}: {value}" for key, value in USAGES.items()]),
    type="application",
    homepage="https://github.com/WindowsSov8forUs/nonebot-plugin-tsugu-bangdream-bot",
    config=Config,
)
