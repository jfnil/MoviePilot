from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class TransferTorrent(BaseModel):
    """
    待转移任务信息
    """
    title: Optional[str] = None
    path: Optional[Path] = None
    hash: Optional[str] = None
    tags: Optional[str] = None


class DownloadingTorrent(BaseModel):
    """
    下载中任务信息
    """
    hash: Optional[str] = None
    title: Optional[str] = None
    name: Optional[str] = None
    year: Optional[str] = None
    season_episode: Optional[str] = None
    size: Optional[float] = 0
    progress: Optional[float] = 0
    state: Optional[str] = 'downloading'
    upspeed: Optional[str] = None
    dlspeed: Optional[str] = None
    media: Optional[dict] = {}


class TransferInfo(BaseModel):
    """
    文件转移结果信息
    """
    # 转移⼁路径
    path: Optional[Path] = None
    # 转移后路径
    target_path: Optional[Path] = None
    # 是否蓝光原盘
    is_bluray: Optional[bool] = False
    # 处理文件数
    file_count: Optional[int] = 0
    # 处理文件清单
    file_list: Optional[list] = []
    # 总文件大小
    total_size: Optional[float] = 0
    # 失败清单
    fail_list: Optional[list] = []
    # 错误信息
    message: Optional[str] = None
