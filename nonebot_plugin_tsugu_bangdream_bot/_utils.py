from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from tsugu_api_core._typing import ServerId, ServerName

TIER_LISTS = {
    "jp": [20, 30, 40, 50, 100, 200, 300, 400, 500, 1000, 2000, 5000, 10000, 20000, 30000, 50000],
    "tw": [100, 500],
    "en": [50, 100, 300, 500, 1000, 2000, 2500],
    "kr": [100],
    "cn": [20, 30, 40, 50, 100, 200, 300, 400, 500, 1000, 2000, 3000, 4000, 5000, 10000, 20000, 30000, 50000]
}

def tier_list_of_server_to_string() -> str:
    results: List[str] = []
    for server, tiers in TIER_LISTS.items():
        results.append(server + " : " + ", ".join(str(tier) for tier in tiers))
    return "\n".join(results)

USAGES = {
    "开启车牌转发": "开启车牌转发",
    "关闭车牌转发": "关闭车牌转发",
    "绑定玩家信息": """绑定玩家 [server_name:str]
开始玩家数据绑定流程，请不要在"绑定玩家"指令后添加玩家ID。省略服务器名时，默认为绑定到你当前的主服务器。请在获得临时验证数字后，将玩家签名改为该数字，并回复你的玩家ID""",
    "解除当前服务器的玩家绑定": """解除绑定 [server_name:str]
解除指定服务器的玩家数据绑定。省略服务器名时，默认为当前的主服务器""",
    "设置主服务器": """
主服务器 <server_name:str>
将指定的服务器设置为你的主服务器
示例:
    主服务器 cn : 将国服设置为主服务器
    日服模式 : 将日服设置为主服务器""",
    "设定信息显示中的默认服务器排序": """设置默认服务器 <server_list:str+:>
使用空格分隔服务器列表
示例:
    设置默认服务器 国服 日服 : 将国服设置为第一服务器，日服设置为第二服务器""",
    "查询自己的玩家状态": """玩家状态 [server_name:str]
查询自己的玩家状态""",
    "获取车牌": """ycm [keyword:str+:]
获取所有车牌车牌，可以通过关键词过滤
示例:
    ycm : 获取所有车牌
    ycm 大分: 获取所有车牌，其中包含"大分"关键词的车牌""",
    "查询玩家信息": """查玩家 <player_id:int> [server_name:str]
查询指定ID玩家的信息。省略服务器名时，默认从你当前的主服务器查询
示例:
    查玩家 10000000 : 查询你当前默认服务器中，玩家ID为10000000的玩家信息
    查玩家 40474621 jp : 查询日服玩家ID为40474621的玩家信息""",
    "查卡": """查卡 <word:str+:>
根据关键词或卡牌ID查询卡片信息，请使用空格隔开所有参数
示例:
    查卡 1399 :返回1399号卡牌的信息
    查卡 绿 tsugu :返回所有属性为pure的羽泽鸫的卡牌列表""",
    "查卡面": """查卡面 <card_id:int>
根据卡片ID查询卡片插画
示例:
    查卡面 1399 :返回1399号卡牌的插画""",
    "查角色": """查角色 <word:str+>
根据关键词或角色ID查询角色信息
示例:
    查角色 10 :返回10号角色的信息
    查角色 吉他 :返回所有角色模糊搜索标签中包含吉他的角色列表""",
    "查活动": """查活动 <word:str+>
根据关键词或活动ID查询活动信息
示例:
    查活动 177 :返回177号活动的信息
    查活动 绿 tsugu :返回所有属性加成为pure，且活动加成角色中包括羽泽鸫的活动列表""",
    "查曲": """查曲 <word:str+>
根据关键词或曲目ID查询曲目信息
示例:
    查曲 1 :返回1号曲的信息
    查曲 ag lv27 :返回所有难度为27的ag曲列表""",
    "查谱面": """查谱面 <song_id:int> [difficulty:str]
根据曲目ID与难度查询谱面信息
示例:
    查谱面 1 :返回1号曲的所有谱面
    查谱面 1 expert :返回1号曲的expert难度谱面""",
    "查询分数表": """查询分数表 <word:str+>
查询指定服务器的歌曲分数表，如果没有服务器名的话，服务器为用户的默认服务器
示例:
    查询分数表 cn :返回国服的歌曲分数表""",
    "查试炼": """查试炼 [event_id:int]
查询当前服务器当前活动试炼信息
示例:
    查试炼 157 -m :返回157号活动的试炼信息，包含歌曲meta
    查试炼 -m :返回当前活动的试炼信息，包含歌曲meta
    查试炼 :返回当前活动的试炼信息""",
    "查卡池": """查卡池 <gacha_id:int>
根据卡池ID查询卡池信息""",
    "查询指定档位的预测线": f"""ycx <tier:int> [event_id:int] [server_name:str]
查询指定档位的预测线，如果没有服务器名的话，服务器为用户的默认服务器。如果没有活动ID的话，活动为当前活动
可用档线:
{tier_list_of_server_to_string()}
示例:
    ycx 1000 :返回默认服务器当前活动1000档位的档线与预测线
    ycx 1000 177 jp:返回日服177号活动1000档位的档线与预测线""",
    "查询所有档位的预测线": f"""ycxall [event_id:int] [server_name:str]
查询所有档位的预测线，如果没有服务器名的话，服务器为用户的默认服务器。如果没有活动ID的话，活动为当前活动
可用档线:
{tier_list_of_server_to_string()}""",
    "查询指定档位的预测线": f"""lsycx <tier:int> [event_id:int] [server_name:str]
查询指定档位的预测线，与最近的4期活动类型相同的活动的档线数据，如果没有服务器名的话，服务器为用户的默认服务器。如果没有活动ID的话，活动为当前活动
可用档线:
{tier_list_of_server_to_string()}
示例:
    lsycx 1000 :返回默认服务器当前活动的档线与预测线，与最近的4期活动类型相同的活动的档线数据
    lsycx 1000 177 jp:返回日服177号活动1000档位档线与最近的4期活动类型相同的活动的档线数据""",
    "抽卡模拟": """抽卡模拟 [times:int] [gacha_id:int]
模拟抽卡，如果没有卡池ID的话，卡池为当前活动的卡池
示例:
    抽卡模拟:模拟抽卡10次
    抽卡模拟 300 922 :模拟抽卡300次，卡池为922号卡池"""
}

def server_name_to_id(server: str) -> 'ServerId':
    if server == "0":
        return 0
    elif server == "1":
        return 1
    elif server == "2":
        return 2
    elif server == "3":
        return 3
    elif server == "4":
        return 4
    elif server == "日服":
        return 0
    elif server == "国际服":
        return 1
    elif server == "台服":
        return 2
    elif server == "国服":
        return 3
    elif server == "韩服":
        return 4
    elif server == "jp":
        return 0
    elif server == "en":
        return 1
    elif server == "tw":
        return 2
    elif server == "cn":
        return 3
    elif server == "kr":
        return 4
    else:
        raise ValueError("服务器不存在")

def server_id_to_full_name(server: 'ServerId') -> str:
    if server == 0:
        return "日服"
    elif server == 1:
        return "国际服"
    elif server == 2:
        return "台服"
    elif server == 3:
        return "国服"
    elif server == 4:
        return "韩服"
    else:
        raise ValueError("服务器不存在")

def server_id_to_short_name(server: 'ServerId') -> 'ServerName':
    if server == 0:
        return "jp"
    elif server == 1:
        return "en"
    elif server == 2:
        return "tw"
    elif server == 3:
        return "cn"
    elif server == 4:
        return "kr"
    else:
        raise ValueError("服务器不存在")
