from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Sequence
from sqlalchemy.orm import Session

from app.db.models import Base


class Site(Base):
    """
    站点表
    """
    id = Column(Integer, Sequence('id'), primary_key=True, index=True)
    # 站点名
    name = Column(String, nullable=False)
    # 域名Key
    domain = Column(String, index=True)
    # 站点地址
    url = Column(String, nullable=False)
    # 站点优先级
    pri = Column(Integer, default=1)
    # RSS地址，未启用
    rss = Column(String)
    # Cookie
    cookie = Column(String)
    # User-Agent
    ua = Column(String)
    # 是否使用代理 0-否，1-是
    proxy = Column(Integer)
    # 过滤规则
    filter = Column(String)
    # 是否渲染
    render = Column(Integer)
    # 是否公开站点
    public = Column(Integer)
    # 附加信息
    note = Column(String)
    # 流控单位周期
    limit_interval = Column(Integer, default=0)
    # 流控次数
    limit_count = Column(Integer, default=0)
    # 流控间隔
    limit_seconds = Column(Integer, default=0)
    # 是否启用
    is_active = Column(Boolean(), default=True)
    # 创建时间
    lst_mod_date = Column(String, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def get_by_domain(db: Session, domain: str):
        return db.query(Site).filter(Site.domain == domain).first()

    @staticmethod
    def get_actives(db: Session):
        return db.query(Site).filter(Site.is_active == 1).all()

    @staticmethod
    def list_order_by_pri(db: Session):
        return db.query(Site).order_by(Site.pri).all()

    @staticmethod
    def reset(db: Session):
        db.query(Site).delete()
        db.commit()
