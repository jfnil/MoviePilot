from pathlib import Path
from threading import Event
from typing import List, Tuple, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.context import MediaInfo
from app.core.metainfo import MetaInfo
from app.helper.nfo import NfoReader
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import MediaType
from app.utils.system import SystemUtils


class LibraryScraper(_PluginBase):

    # 插件名称
    plugin_name = "媒体库刮削"
    # 插件描述
    plugin_desc = "定时对媒体库进行刮削，补齐缺失元数据和图片。"
    # 插件图标
    plugin_icon = "scraper.png"
    # 主题色
    plugin_color = "#FF7D00"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jxxghp"
    # 作者主页
    author_url = "https://github.com/jxxghp"
    # 插件配置项ID前缀
    plugin_config_prefix = "libraryscraper_"
    # 加载顺序
    plugin_order = 7
    # 可使用的用户级别
    user_level = 1

    # 私有属性
    _scheduler = None
    _scraper = None
    # 限速开关
    _enabled = False
    _cron = None
    _scraper_paths = ""
    _exclude_paths = ""
    # 退出事件
    _event = Event()
    
    def init_plugin(self, config: dict = None):
        # 读取配置
        if config:
            self._enabled = config.get("enabled")
            self._cron = config.get("cron")
            self._scraper_paths = config.get("scraper_paths") or ""
            self._exclude_paths = config.get("exclude_paths") or ""

        # 停止现有任务
        self.stop_service()

        # 启动定时任务 & 立即运行一次
        if self._enabled:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            if self._cron:
                logger.info(f"媒体库刮削服务启动，周期：{self._cron}")
                try:
                    self._scheduler.add_job(self.__libraryscraper,
                                            CronTrigger.from_crontab(self._cron))
                except Exception as e:
                    logger.error(f"媒体库刮削服务启动失败，原因：{e}")
                    self.systemmessage.put(f"媒体库刮削服务启动失败，原因：{e}")
            else:
                logger.info(f"媒体库刮削服务启动，周期：每7天")
                self._scheduler.add_job(self.__libraryscraper,
                                        CronTrigger.from_crontab("0 0 */7 * *"))
            if self._scheduler.get_jobs():
                # 启动服务
                self._scheduler.print_jobs()
                self._scheduler.start()

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '执行周期',
                                            'placeholder': '5位cron表达式，留空自动'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'scraper_paths',
                                            'label': '削刮路径',
                                            'rows': 5,
                                            'placeholder': '每一行一个目录'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'exclude_paths',
                                            'label': '排除路径',
                                            'rows': 2,
                                            'placeholder': '每一行一个目录'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "cron": "0 0 */7 * *",
            "scraper_paths": "",
            "err_hosts": ""
        }

    def get_page(self) -> List[dict]:
        pass

    def __libraryscraper(self):
        """
        开始刮削媒体库
        """
        if not self._scraper_paths:
            return
        # 已选择的目录
        paths = self._scraper_paths.split("\n")
        for path in paths:
            if not path:
                continue
            if not Path(path).exists():
                logger.warning(f"媒体库刮削路径不存在：{path}")
                continue
            logger.info(f"开始刮削媒体库：{path} ...")
            if self._event.is_set():
                logger.info(f"媒体库刮削服务停止")
                return
            # 刮削目录
            self.__scrape_dir(Path(path))
            logger.info(f"媒体库刮削完成")

    def __scrape_dir(self, path: Path):
        """
        削刮一个目录
        """
        exclude_paths = self._exclude_paths.split("\n")
        # 查找目录下所有的文件
        files = SystemUtils.list_files_with_extensions(path, settings.RMT_MEDIAEXT)
        for file in files:
            # 排除目录
            exclude_flag = False
            for exclude_path in exclude_paths:
                if file.is_relative_to(Path(exclude_path)):
                    exclude_flag = True
                    break
            if exclude_flag:
                logger.debug(f"{file} 在排除目录中，跳过 ...")
                continue
            # 识别媒体文件
            meta_info = MetaInfo(file.name)
            # 优先读取本地nfo文件
            tmdbid = None
            if meta_info.type == MediaType.MOVIE:
                # 电影
                movie_nfo = file.parent / "movie.nfo"
                if movie_nfo.exists():
                    tmdbid = self.__get_tmdbid_from_nfo(movie_nfo)
                file_nfo = file.with_suffix(".nfo")
                if not tmdbid and file_nfo.exists():
                    tmdbid = self.__get_tmdbid_from_nfo(file_nfo)
            else:
                # 电视剧
                tv_nfo = file.parent.parent / "tvshow.nfo"
                if tv_nfo.exists():
                    tmdbid = self.__get_tmdbid_from_nfo(tv_nfo)
            if tmdbid:
                logger.info(f"读取到本地nfo文件的tmdbid：{tmdbid}")
                # 识别媒体信息
                mediainfo: MediaInfo = self.chain.recognize_media(tmdbid=tmdbid, mtype=meta_info.type)
            else:
                # 识别媒体信息
                mediainfo: MediaInfo = self.chain.recognize_media(meta=meta_info)
            if not mediainfo:
                logger.warn(f"未识别到媒体信息：{file}")
                continue
            # 开始刮削
            self.chain.scrape_metadata(path=path, mediainfo=mediainfo)

    @staticmethod
    def __get_tmdbid_from_nfo(file_path: Path):
        """
        从nfo文件中获取信息
        :param file_path:
        :return: tmdbid
        """
        if not file_path:
            return None
        xpaths = [
            "uniqueid[@type='Tmdb']",
            "uniqueid[@type='tmdb']",
            "uniqueid[@type='TMDB']",
            "tmdbid"
        ]
        reader = NfoReader(file_path)
        for xpath in xpaths:
            try:
                tmdbid = reader.get_element_value(xpath)
                if tmdbid:
                    return tmdbid
            except Exception as err:
                print(str(err))
        return None

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._event.set()
                    self._scheduler.shutdown()
                    self._event.clear()
                self._scheduler = None
        except Exception as e:
            print(str(e))
