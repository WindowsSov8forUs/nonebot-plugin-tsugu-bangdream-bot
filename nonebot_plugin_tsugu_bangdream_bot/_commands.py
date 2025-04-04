from base64 import b64decode
from typing import TYPE_CHECKING, List, Type, Union, Optional

from nonebot import logger

from nonebot_plugin_alconna import Text, Image, Segment, UniMessage, AlconnaMatcher

import tsugu_api_async
from tsugu_api_core.exception import FailedException

if TYPE_CHECKING:
    
    from tsugu_api_core._typing import (
        _Response,
        ServerId,
        _TsuguUser,
        _DifficultyId,
        _UserPlayerInList,
        FuzzySearchResult
    )

from .config import CAR, FAKE

from ._utils import server_id_to_full_name

def _list_to_message(response: '_Response') -> UniMessage:
    segments: List[Segment] = []
    for _r in response:
        if _r["type"] == "string":
            segments.append(Text(_r["string"]))
        else:
            segments.append(Image(raw=b64decode(_r["string"])))
    
    return UniMessage(segments)

async def _get_tsugu_user(platform: str, user_id: str) -> '_TsuguUser':
    try:
        response = await tsugu_api_async.get_user_data(platform, user_id)
    except FailedException as exception:
        raise exception
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to get user data')
        raise Exception(f"错误: {exception}") from exception
    
    return response["data"]

def _get_user_player_from_tsugu_user(tsugu_user: '_TsuguUser', server: Optional['ServerId']=None, index: Optional[int]=None) -> '_UserPlayerInList':
    server = server or tsugu_user["mainServer"]
    user_player_list = tsugu_user["userPlayerList"]
    user_player_index = index or tsugu_user["userPlayerIndex"]
    
    if len(user_player_list) == 0:
        raise ValueError("用户未绑定player")
    
    if index is not None:
        return user_player_list[index]
    
    if tsugu_user["userPlayerList"][user_player_index]["server"] == server:
        return tsugu_user["userPlayerList"][user_player_index]
    
    for user_player in user_player_list:
        if user_player["server"] == server:
            return user_player
    
    raise ValueError("用户在对应服务器上未绑定player")

async def forward_room(
    room_number: int,
    raw_message: str,
    tsugu_user: '_TsuguUser',
    platform: str,
    user_id: str,
    user_name: str,
    bandori_station_token: Optional[str]
) -> bool:
    if not tsugu_user["shareRoomNumber"]:
        logger.debug("User is disabled to forward room number")
        return False
    
    is_car: bool = False
    for _car in CAR:
        if _car in raw_message:
            is_car = True
            break
    
    if not is_car:
        return False
    
    for _fake in FAKE:
        if _fake in raw_message:
            logger.debug(f"Invalid keyword in message: {_fake}")
            return False
    
    try:
        response = await tsugu_api_async.station_submit_room_number(
            room_number,
            raw_message,
            platform,
            user_id,
            user_name,
            bandori_station_token
        )
    except Exception as exception:
        logger.warning(f"Failed to submit room number: {exception}")
        return False
    
    if response["status"] == "success":
        return True
    else:
        logger.warning(f"Failed to submit room number: {response['data']}")
        return False

async def switch_forward(platform: str, user_id: str, mode: bool) -> str:
    try:
        await tsugu_api_async.change_user_data(
            platform,
            user_id,
            {"shareRoomNumber": mode}
        )
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to change user data')
        return f"错误: {exception}"
    
    return (
        "已"
        + ("开启" if mode else "关闭")
        + "车牌转发"
    )

async def player_bind(matcher: Type[AlconnaMatcher], platform: str, user_id: str, server: 'ServerId') -> None:
    try:
        response = await tsugu_api_async.bind_player_request(platform, user_id)
    except FailedException as exception:
        return await matcher.finish(exception.response["data"])
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to request for binding player')
        return await matcher.finish(f"错误: {exception}")
    
    verify_code = response["data"]["verifyCode"]
    matcher.set_path_arg("verify_server", server)
    
    return await matcher.send(
        f"正在绑定来自 {server_id_to_full_name(server)} 账号，"
        + "请将你的\n评论(个性签名)\n或者\n你的当前使用的卡组的卡组名(乐队编队名称)\n改为以下数字后，直接发送你的玩家id\n"
        + f"{verify_code}"
    )

async def player_unbind(matcher: Type[AlconnaMatcher], platform: str, user_id: str, server: 'ServerId', index: Optional[int]=None) -> None:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except FailedException as exception:
        return await matcher.finish(exception.response["data"])
    except Exception as exception:
        return await matcher.finish(f"错误: {exception}")
    
    try:
        player = _get_user_player_from_tsugu_user(tsugu_user, server)
    except Exception as exception:
        return await matcher.finish(str(exception))
    player_id = player["playerId"]
    
    if server is None:
        server = tsugu_user["mainServer"]
    
    try:
        response = await tsugu_api_async.bind_player_request(platform, user_id)
    except FailedException as exception:
        return await matcher.finish(exception.response["data"])
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to request for unbinding player')
        return await matcher.finish(f"错误: {exception}")
    
    verify_code = response["data"]["verifyCode"]
    matcher.set_path_arg("verify_server", server)
    matcher.set_path_arg("player_id", player_id)
    return await matcher.send(
        f"正在解除绑定来自 {server_id_to_full_name(server)} 账号 玩家ID: {player_id} \n"
        + "请将你的\n评论(个性签名)\n或者\n你的当前使用的卡组的卡组名(乐队编队名称)\n改为以下数字后，发送任意消息继续\n"
        + f"{verify_code}"
    )

async def switch_main_server(platform: str, user_id: str, server: 'ServerId') -> str:
    try:
        response = await tsugu_api_async.change_user_data(
            platform,
            user_id,
            {"mainServer": server}
        )
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to change main server')
        return f"错误: {exception}"
    
    if response["status"] == "failed":
        assert "data" in response
        return response["data"]
    
    return (
        f"已切换到{server_id_to_full_name(server)}模式"
    )

async def set_default_servers(platform: str, user_id: str, servers: List['ServerId']) -> str:
    try:
        response = await tsugu_api_async.change_user_data(
            platform,
            user_id,
            {"displayedServerList": servers}
        )
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to change default servers')
        return f"错误: {exception}"
    
    if response["status"] == "failed":
        assert "data" in response
        return response["data"]
    
    return (
        f"成功切换默认显示服务器顺序: {', '.join(server_id_to_full_name(server) for server in servers)}"
    )

async def player_info(platform: str, user_id: str, index: Optional[int]=None, server_name: Optional[str]=None) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    player_list = tsugu_user["userPlayerList"]
    if len(player_list) < 1:
        return "未绑定任何玩家"
    
    if index is None:
        if server_name is None:
            try:
                player = _get_user_player_from_tsugu_user(tsugu_user, tsugu_user["mainServer"])
            except Exception as exception:
                return str(exception)
        else:
            try:
                server = await server_name_fuzzy_search(server_name)
            except ValueError as exception:
                return str(exception)
            
            try:
                player = _get_user_player_from_tsugu_user(tsugu_user, server)
            except Exception as exception:
                return str(exception)
    else:
        if index > len(player_list) or index < 1:
            return "错误: 无效的绑定信息ID"
        player = player_list[index - 1]
    
    return await search_player(platform, user_id, player["playerId"], player["server"])

async def get_player_list(platform: str, user_id: str) -> str:
    result: str = ""
    
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    player_list = tsugu_user["userPlayerList"]
    if len(player_list) < 1:
        result += "未绑定任何玩家\n"
    else:
        result += "已绑定玩家列表:\n"
        
        for index, player in enumerate(player_list):
            result += f"{index + 1}. {server_id_to_full_name(player['server'])}: {player['playerId']}\n"
        result += f"当前默认玩家绑定信息ID: {tsugu_user['userPlayerIndex'] + 1}\n"
    
    result += (
        f"当前主服务器: {server_id_to_full_name(tsugu_user['mainServer'])}\n"
        + f"默认显示服务器顺序: {', '.join(server_id_to_full_name(server) for server in tsugu_user['displayedServerList'])}\n"
    )
    
    return result

async def switch_player_index(platform: str, user_id: str, index: int) -> str:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    if index > len(tsugu_user["userPlayerList"]) or index < 1:
        return "错误: 无效的绑定信息ID"
    
    try:
        await tsugu_api_async.change_user_data(
            platform,
            user_id,
            {"userPlayerIndex": index - 1}
        )
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to change user player index')
        return f"错误: {exception}"
    
    return f"已切换至绑定信息ID: {index}"

async def search_player(platform: str, user_id: str, player_id: int, server: Optional['ServerId']=None) -> Union[str, UniMessage]:
    if server is None:
        try:
            tsugu_user = await _get_tsugu_user(platform, user_id)
        except Exception as exception:
            return str(exception)
        
        server = tsugu_user["mainServer"]
    
    try:
        return _list_to_message(await tsugu_api_async.search_player(player_id, server))
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search player')
        return f"错误: {exception}"

async def room_list(keyword: Optional[str]=None) -> Union[str, UniMessage]:
    try:
        _response = await tsugu_api_async.station_query_all_room()
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to query all room')
        return f"错误: {exception}"
    
    try:
        response = await tsugu_api_async.room_list(_response["data"])
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to request for rendering room list')
        return f"错误: {exception}"
    
    return _list_to_message(response)

async def search_card(platform: str, user_id: str, word: str) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    servers = tsugu_user["displayedServerList"]
    
    try:
        response = await tsugu_api_async.search_card(servers, word)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search card')
        return f"错误: {exception}"
    
    return _list_to_message(response)

async def get_card_illustration(card_id: int) -> Union[str, UniMessage]:
    try:
        response = await tsugu_api_async.get_card_illustration(card_id)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to get card illustration')
        return f"错误: {exception}"
    
    return _list_to_message(response)

async def search_character(platform: str, user_id: str, text: str) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    servers = tsugu_user["displayedServerList"]
    
    try:
        response = await tsugu_api_async.search_character(servers, text=text)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search character')
        return f"错误: {exception}"
    
    return _list_to_message(response)

async def search_event(platform: str, user_id: str, text: str) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    servers = tsugu_user["displayedServerList"]

    try:
        response = await tsugu_api_async.search_event(servers, text=text)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search event')
        return f"错误: {exception}"
    
    return _list_to_message(response)

async def search_song(platform: str, user_id: str, text: str) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    servers = tsugu_user["displayedServerList"]
    
    try:
        response = await tsugu_api_async.search_song(servers, text=text)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search song')
        return f"错误: {exception}"
    
    return _list_to_message(response)

async def song_chart(platform: str, user_id: str, song_id: int, difficulty_id: '_DifficultyId') -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    servers = tsugu_user["displayedServerList"]

    try:
        response = await tsugu_api_async.song_chart(servers, song_id, difficulty_id)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to get song chart')
        return f"错误: {exception}"
    
    return _list_to_message(response)

async def random_song(platform: str, user_id: str, text: str) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    main_server = tsugu_user["mainServer"]

    try:
        response = await tsugu_api_async.song_random(main_server, text=text)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to get random song')
        return f"错误: {exception}"
    
    return _list_to_message(response)

async def song_meta(platform: str, user_id: str, server: Optional['ServerId']=None) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    servers = tsugu_user["displayedServerList"]
    if server is None:
        server = tsugu_user["mainServer"]

    try:
        response = await tsugu_api_async.song_meta(servers, server)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to get song meta')
        return f"错误: {exception}"

    return _list_to_message(response)

async def event_stage(platform: str, user_id: str, event_id: Optional[int]=None, meta: bool=False) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    server = tsugu_user["mainServer"]

    try:
        response = await tsugu_api_async.event_stage(server, event_id, meta)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to get event stage')
        return f"错误: {exception}"

    return _list_to_message(response)

async def search_gacha(platform: str, user_id: str, gacha_id: int) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    servers = tsugu_user["displayedServerList"]

    try:
        response = await tsugu_api_async.search_gacha(servers, gacha_id)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search gacha')
        return f"错误: {exception}"

    return _list_to_message(response)

async def search_ycx(platform: str, user_id: str, tier: int, event_id: Optional[int]=None, server: Optional['ServerId']=None) -> Union[str, UniMessage]:
    if server is None:
        try:
            tsugu_user = await _get_tsugu_user(platform, user_id)
        except Exception as exception:
            return str(exception)
        
        server = tsugu_user["mainServer"]
    
    try:
        response = await tsugu_api_async.cutoff_detail(server, tier, event_id)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search cutoff')
        return f"错误: {exception}"

    return _list_to_message(response)

async def search_ycx_all(platform: str, user_id: str, server: Optional['ServerId']=None, event_id: Optional[int]=None) -> Union[str, UniMessage]:
    if server is None:
        try:
            tsugu_user = await _get_tsugu_user(platform, user_id)
        except Exception as exception:
            return str(exception)
        
        server = tsugu_user["mainServer"]
    
    try:
        response = await tsugu_api_async.cutoff_all(server, event_id)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search all cutoff')
        return f"错误: {exception}"

    return _list_to_message(response)

async def search_lsycx(platform: str, user_id: str, tier: int, event_id: Optional[int]=None, server: Optional['ServerId']=None) -> Union[str, UniMessage]:
    if server is None:
        try:
            tsugu_user = await _get_tsugu_user(platform, user_id)
        except Exception as exception:
            return str(exception)
        
        server = tsugu_user["mainServer"]
    
    try:
        response = await tsugu_api_async.cutoff_list_of_recent_event(server, tier, event_id)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to search cutoff history')
        return f"错误: {exception}"

    return _list_to_message(response)

async def simulate_gacha(platform: str, user_id: str, times: Optional[int]=None, gacha_id: Optional[int]=None) -> Union[str, UniMessage]:
    try:
        tsugu_user = await _get_tsugu_user(platform, user_id)
    except Exception as exception:
        return str(exception)
    
    server = tsugu_user["mainServer"]

    try:
        response = await tsugu_api_async.gacha_simulate(server, times, gacha_id)
    except FailedException as exception:
        return exception.response["data"]
    except Exception as exception:
        logger.opt(exception=exception).debug('Failed to simulate gacha')
        return f"错误: {exception}"

    return _list_to_message(response)

async def get_fuzzy_search_result(text: str) -> 'FuzzySearchResult':
    try:
        response = await tsugu_api_async.fuzzy_search(text)
    except:
        return {}
    
    return response["data"]

async def server_name_fuzzy_search(server_name: str) -> 'ServerId':
    result = await get_fuzzy_search_result(server_name)
    result_server = result.get("server", [])
    if len(result_server) < 1 or not result_server[0] in (0, 1, 2, 3, 4):
        raise ValueError("未找到服务器")
    
    return result_server[0]

async def difficulty_id_fuzzy_search(difficulty_name: str) -> '_DifficultyId':
    if difficulty_name in ("ez", "easy", "简单"):
        return 0
    if difficulty_name in ("nm", "normal", "普通"):
        return 1
    if difficulty_name in ("hd", "hard", "困难"):
        return 2
    if difficulty_name in ("ex", "expert", "专家"):
        return 3
    if difficulty_name in ("sp", "special", "特殊"):
        return 4
    
    result = await get_fuzzy_search_result(difficulty_name)
    if "difficulty" not in result or result["difficulty"][0] not in (0, 1, 2, 3, 4):
        raise ValueError("错误: 难度名未能匹配任何难度")
    
    return result["difficulty"][0]
