from base64 import b64decode
from typing import List, Tuple, Union, Optional, Sequence

import tsugu_api_async
from tsugu_api_async._typing import _Server, _ServerId, _DifficultyText

from ._utils import server_id_to_full_name

async def switch_forward(user_id: str, mode: bool) -> str:
    try:
        response = await tsugu_api_async.change_user_data(
            "red",
            user_id,
            {'car': mode}
        )
    except Exception as exception:
        return f"错误: {exception}"
    
    if response["status"] == "failed":
        assert "data" in response
        return response["data"]
    else:
        return (
            "已"
            + ("开启" if mode else "关闭")
            + "车牌转发"
        )

async def player_bind(user_id: str, server: Optional[_ServerId]=None) -> Tuple[str, bool, Optional[_ServerId]]:
    if server is None:
        try:
            _response = await tsugu_api_async.get_user_data("red", user_id)
        except Exception as exception:
            return f"错误: {exception}", False, None
        
        if _response["status"] == "failed":
            assert isinstance(_response["data"], str)
            return _response["data"], False, None
        
        assert isinstance(_response["data"], dict)
        tsugu_user = _response["data"]
        server = tsugu_user["server_mode"]
    
    try:
        response = await tsugu_api_async.bind_player_request("red", user_id, server, True)
    except Exception as exception:
        return f"错误: {exception}", False, None
    
    if response["status"] == "failed":
        assert isinstance(response["data"], str)
        return response["data"], False, None
    
    assert isinstance(response["data"], dict)
    verify_code = response["data"]["verifyCode"]
    return (
        f"正在绑定 {server_id_to_full_name(server)} 账号，"
        + "请将你的\n评论(个性签名)\n或者\n你的当前使用的卡组的卡组名(乐队编队名称)\n改为以下数字后，直接发送你的玩家id\n"
        + f"{verify_code}"
    ), True, server

async def player_unbind(user_id: str, server: Optional[_ServerId]=None) -> Tuple[str, bool, Optional[_ServerId], Optional[int]]:
    try:
        _response = await tsugu_api_async.get_user_data("red", user_id)
    except Exception as exception:
        return f"错误: {exception}", False, None, None
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        return _response["data"], False, None, None
    
    assert isinstance(_response["data"], dict)
    tsugu_user = _response["data"]
    
    if server is None:
        server = tsugu_user["server_mode"]
    
    tsugu_user_server = tsugu_user["server_list"][server]
    
    try:
        response = await tsugu_api_async.bind_player_request("red", user_id, server, False)
    except Exception as exception:
        return f"错误: {exception}", False, None, None
    
    if response["status"] == "failed":
        assert isinstance(response["data"], str)
        return response["data"], False, None, None
    
    assert isinstance(response["data"], dict)
    verify_code = response["data"]["verifyCode"]
    return (
        f"正在解除绑定 {server_id_to_full_name(server)} 账号 {tsugu_user_server['playerId']} \n"
        + f"因为使用远程服务器，解除绑定需要验证\n请将 {tsugu_user_server['playerId']} 账号的\n"
        + "评论(个性签名)\n或者\n你的当前使用的卡组的卡组名(乐队编队名称)\n改为以下数字后，发送任意消息继续\n"
        + f"{verify_code}"
    ), True, server, tsugu_user_server["playerId"]

async def switch_main_server(user_id: str, server: _ServerId) -> str:
    try:
        response = await tsugu_api_async.change_user_data(
            "red",
            user_id,
            {'server_mode': server}
        )
    except Exception as exception:
        return f"错误: {exception}"
    
    if response["status"] == "failed":
        assert "data" in response
        return response["data"]
    
    return (
        f"已切换到{server_id_to_full_name(server)}模式"
    )

async def set_default_servers(user_id: str, servers: List[_ServerId]) -> str:
    try:
        response = await tsugu_api_async.change_user_data(
            "red",
            user_id,
            {"default_server": servers}
        )
    except Exception as exception:
        return f"错误: {exception}"
    
    if response["status"] == "failed":
        assert "data" in response
        return response["data"]
    
    return (
        f"成功切换默认服务器顺序: {', '.join(server_id_to_full_name(server) for server in servers)}"
    )

async def player_info(user_id: str, server: Optional[_ServerId]=None) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.get_user_data("red", user_id)
    except Exception as exception:
        return [f"错误: {exception}"]
    
    if response["status"] == "failed":
        assert isinstance(response["data"], str)
        return [response["data"]]
    
    assert isinstance(response["data"], dict)
    tsugu_user = response["data"]
    
    if server is None:
        assert isinstance(tsugu_user["server_mode"], int)
        server = tsugu_user["server_mode"]
    
    if (user_server := tsugu_user["server_list"][server])["bindingStatus"] != 2:
        return [f"错误: 未检测到{server_id_to_full_name(server)}的玩家数据"]
    
    return await search_player(user_server["playerId"], server)
    
async def search_player(player_id: int, server: _Server) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.search_player(player_id, server)
    except Exception as exception:
        return [f"错误: {exception}"]
    
    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def room_list(keyword: Optional[str]=None) -> List[Union[str, bytes]]:
    try:
        _response = await tsugu_api_async.station_query_all_room()
    except Exception as exception:
        return [f"错误: {exception}"]
    
    if _response["status"] == "failed":
        assert isinstance(_response["data"], str)
        return [_response["data"]]
    
    assert isinstance(_response["data"], list)
    try:
        response = await tsugu_api_async.room_list(_response["data"])
    except Exception as exception:
        return [f"错误: {exception}"]
    
    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def search_card(word: str, servers: Sequence[_Server]) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.search_card(servers, word)
    except Exception as exception:
        return [f"错误: {exception}"]
    
    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def get_card_illustration(card_id: int) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.get_card_illustration(card_id)
    except Exception as exception:
        return [f"错误: {exception}"]
    
    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def search_character(text: str, servers: Sequence[_Server]) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.search_character(servers, text)
    except Exception as exception:
        return [f"错误: {exception}"]
    
    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def search_event(text: str, servers: Sequence[_Server]) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.search_event(servers, text)
    except Exception as exception:
        return [f"错误: {exception}"]
    
    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def search_song(text: str, servers: Sequence[_Server]) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.search_song(servers, text)
    except Exception as exception:
        return [f"错误: {exception}"]
    
    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def song_chart(servers: Sequence[_Server], song_id: int, difficulty_text: _DifficultyText) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.song_chart(servers, song_id, difficulty_text)
    except Exception as exception:
        return [f"错误: {exception}"]
    
    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def song_meta(servers: Sequence[_Server], server: _Server) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.song_meta(servers, server)
    except Exception as exception:
        return [f"错误: {exception}"]

    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def event_stage(server: _Server, event_id: Optional[int]=None, meta: bool=False) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.event_stage(server, event_id, meta)
    except Exception as exception:
        return [f"错误: {exception}"]

    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def search_gacha(servers: Sequence[_Server], gacha_id: int) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.search_gacha(servers, gacha_id)
    except Exception as exception:
        return [f"错误: {exception}"]

    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def search_ycx(server: _Server, tier: int, event_id: Optional[int]=None) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.ycx(server, tier, event_id)
    except Exception as exception:
        return [f"错误: {exception}"]

    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def search_ycx_all(server: _Server, event_id: Optional[int]=None) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.ycx_all(server, event_id)
    except Exception as exception:
        return [f"错误: {exception}"]

    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def search_lsycx(server: _Server, tier: int, event_id: Optional[int]=None) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.lsycx(server, tier, event_id)
    except Exception as exception:
        return [f"错误: {exception}"]

    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result

async def simulate_gacha(server: _Server, times: Optional[int]=None, gacha_id: Optional[int]=None) -> List[Union[str, bytes]]:
    try:
        response = await tsugu_api_async.gacha_simulate(server, times, gacha_id)
    except Exception as exception:
        return [f"错误: {exception}"]

    result: List[Union[str, bytes]] = []
    for _r in response:
        if _r["type"] == "string":
            result.append(_r["string"])
        else:
            result.append(b64decode(_r["string"]))
    
    return result
