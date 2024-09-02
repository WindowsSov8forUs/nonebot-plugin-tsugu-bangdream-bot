from typing import Set, Optional

from pydantic import BaseModel

CAR = [
    "q1",
    "q2",
    "q3",
    "q4",
    "Q1",
    "Q2",
    "Q3",
    "Q4",
    "缺1",
    "缺2",
    "缺3",
    "缺4",
    "差1",
    "差2",
    "差3",
    "差4",
    "3火",
    "三火",
    "3把",
    "三把",
    "打满",
    "清火",
    "奇迹",
    "中途",
    "大e",
    "大分e",
    "exi",
    "大分跳",
    "大跳",
    "大a",
    "大s",
    "大分a",
    "大分s",
    "长途",
    "生日车",
    "军训",
    "禁fc"
]

FAKE = [
    "114514",
    "野兽",
    "恶臭",
    "1919",
    "下北泽",
    "粪",
    "糞",
    "臭",
    "11451",
    "xiabeize",
    "雀魂",
    "麻将",
    "打牌",
    "maj",
    "麻",
    "[",
    "]",
    "断幺",
    "qq.com",
    "腾讯会议",
    "master",
    "疯狂星期四",
    "离开了我们",
    "日元",
    "av",
    "bv"
]

class Config(BaseModel):
    """Plugin Config Here"""
    tsugu_use_easy_bg: bool = False
    tsugu_compress: bool = False
    tsugu_bandori_station_token: Optional[str] = None
    
    tsugu_reply: bool = False
    tsugu_at: bool = False
    tsugu_no_space: bool = False
    
    tsugu_backend_url: str = ""
    tsugu_data_backend_url: str = ""
    
    tsugu_proxy: str = ""
    tsugu_backend_proxy: bool = False
    tsugu_data_backend_proxy: bool = False
    tsugu_timeout: int = 10
    
    tsugu_open_forward_aliases: Set[str] = set()
    tsugu_close_forward_aliases: Set[str] = set()
    tsugu_bind_player_aliases: Set[str] = set()
    tsugu_unbind_player_aliases: Set[str] = set()
    tsugu_main_server_aliases: Set[str] = set()
    tsugu_default_servers_aliases: Set[str] = set()
    tsugu_player_status_aliases: Set[str] = set()
    tsugu_player_list_aliases: Set[str] = set()
    tsugu_switch_index_aliases: Set[str] = set()
    tsugu_ycm_aliases: Set[str] = set()
    tsugu_search_player_aliases: Set[str] = set()
    tsugu_search_card_aliases: Set[str] = set()
    tsugu_card_illustration_aliases: Set[str] = set()
    tsugu_search_character_aliases: Set[str] = set()
    tsugu_search_event_aliases: Set[str] = set()
    tsugu_search_song_aliases: Set[str] = set()
    tsugu_song_chart_aliases: Set[str] = set()
    tsugu_song_random_aliases: Set[str] = set()
    tsugu_song_meta_aliases: Set[str] = set()
    tsugu_event_stage_aliases: Set[str] = set()
    tsugu_search_gacha_aliases: Set[str] = set()
    tsugu_ycx_aliases: Set[str] = set()
    tsugu_ycx_all_aliases: Set[str] = set()
    tsugu_lsycx_aliases: Set[str] = set()
    tsugu_gacha_simulate_aliases: Set[str] = set()
