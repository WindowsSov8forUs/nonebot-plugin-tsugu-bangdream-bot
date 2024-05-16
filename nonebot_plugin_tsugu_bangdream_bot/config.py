from typing import Set, Optional

from pydantic import BaseModel


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
    
    tsugu_open_forward_aliases: Set[str] = set()
    tsugu_close_forward_aliases: Set[str] = set()
    tsugu_bind_player_aliases: Set[str] = set()
    tsugu_unbind_player_aliases: Set[str] = set()
    tsugu_main_server_aliases: Set[str] = set()
    tsugu_default_servers_aliases: Set[str] = set()
    tsugu_player_status_aliases: Set[str] = set()
    tsugu_ycm_aliases: Set[str] = set()
    tsugu_search_player_aliases: Set[str] = set()
    tsugu_search_card_aliases: Set[str] = set()
    tsugu_card_illustration_aliases: Set[str] = set()
    tsugu_search_character_aliases: Set[str] = set()
    tsugu_search_event_aliases: Set[str] = set()
    tsugu_search_song_aliases: Set[str] = set()
    tsugu_song_chart_aliases: Set[str] = set()
    tsugu_song_meta_aliases: Set[str] = set()
    tsugu_event_stage_aliases: Set[str] = set()
    tsugu_search_gacha_aliases: Set[str] = set()
    tsugu_ycx_aliases: Set[str] = set()
    tsugu_ycx_all_aliases: Set[str] = set()
    tsugu_lsycx_aliases: Set[str] = set()
    tsugu_gacha_simulate_aliases: Set[str] = set()
