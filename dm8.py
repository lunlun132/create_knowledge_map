from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine,Identity, CheckConstraint
from sqlalchemy import Column, JSON, String, INTEGER, Text, DATETIME, Integer
from sqlalchemy.orm import sessionmaker
# from utilities.config_utils import configs
from sqlalchemy.sql import quoted_name
from sqlalchemy import Column, Integer, String, DateTime, JSON, func, text, Boolean, Float, ForeignKey, BigInteger
from sqlalchemy.dialects.oracle import CLOB
from sqlalchemy.schema import UniqueConstraint, Index
# from models.base import Base
import uuid
import logging
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()
# DATABASE_URL = f'dm+dmPython://{configs.get("database_config_dm", "user", raw=True)}:{configs.get("database_config_dm", "password", raw=True)}@{configs.get("database_config_dm", "host")}:{configs.get("database_config_dm", "port", raw=True)}'
# DATABASE_URL = 'dm+dmPython://SYSDBA:bzcdUhhSn67geB@10.50.21.87:5237/?schema="aico_saas"'
DATABASE_URL = 'dm+dmPython://SYSDBA:bzcdUhhSn67geB@10.50.21.87:5237'
print("使用的 database_url", DATABASE_URL)
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,  # 减小连接池大小以避免过多连接
        max_overflow=20,  # 减小额外连接数
        pool_timeout=10,  # 减小连接超时时间
        pool_recycle=3600,  # 连接回收时间，单位为秒
        pool_pre_ping=True,  # 在获取连接之前，检查连接是否有效
        echo=True
    )
    # 测试连接
    logger.info("正在测试数据库连接...")
    connection = engine.connect()
    connection.close()
    logger.info("数据库连接成功!")
except Exception as e:
    logger.error(f"数据库连接失败: {str(e)}")
    raise
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
# class BusinessInfo(Base):
#     __tablename__ = "business_info"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     business_uuid = Column(String(100), index=True, default=str(uuid.uuid4()), comment='业务类型UUID')
#     business_name = Column(String(300), nullable=False, default="", comment='名称')
#     create_time = Column(DateTime, default=datetime.now, server_default=text("CURRENT_TIMESTAMP"), comment='创建时间')
#     def to_dict(self):
#         return {
#             'id': self.id,
#             'business_uuid': self.business_uuid,
#             'business_name': self.business_name,
#             'create_time': self.create_time
#         }
# class KnowledgeShard(Base):
#     """ 知识分片 """
#     __tablename__ = "knowledge_shard"
#     __table_args__ = (Index('idx_project_kb_id', 'project_id', 'kb_id'),
#                       {"schema": quoted_name("aico_rag", quote=True),"quote": True})
    
#     id = Column("id", INTEGER, Identity(start=1, increment=1), primary_key=True, index=True, comment="数据ID", quote=True)
#     project_id = Column("project_id", INTEGER, index=False, nullable=False, comment="知识所属项目ID", quote=True)
#     kb_id = Column("kb_id", INTEGER, index=False, nullable=False, default=0, comment="知识库关联ID", quote=True)
#     knowledge_id = Column("knowledge_id", INTEGER, index=True, nullable=False, default=0, server_default="0", comment="知识ID", quote=True)
#     chunk_id = Column("chunk_id", INTEGER, index=True, nullable=False, comment="知识片段ID", quote=True)

#     doc_title = Column("doc_title", Text, index=False, nullable=False, default="", comment="文档标题", quote=True)
#     title = Column("title", Text, index=False, nullable=False, default="", comment="标题", quote=True)
#     label = Column("label", Text, index=False, nullable=False, default="",  comment="知识关键词", quote=True)

#     content = Column("content", CLOB, index=False, nullable=True, comment="知识分片内容", quote=True)
#     similar_knowledge = Column(
#         "similar_knowledge", JSON, index=False, nullable=True, default=[], comment="相似问列表", quote=True)
#     create_time = Column("create_time", DATETIME, index=False, nullable=False,
#                          default=datetime.now, server_default=text("SYSDATE"),
#                          comment="知识分片创建时间", quote=True)
#     update_time = Column("update_time", DATETIME, index=False, nullable=False,
#                          default=datetime.now, server_default=text("SYSDATE"),
#                          onupdate=datetime.now,
#                          comment="知识分片修改时间", quote=True)


# import datetime
# from database.mysql.base import Base
from sqlalchemy import Enum as DbEnum
# from sqlalchemy.dialects.mysql import LONGTEXT
# from sqlalchemy.dialects.oracle import CLOB
# from sqlalchemy import Column, String, INTEGER, JSON, DATETIME, Identity
# from model.sys_manage.schemas import PromptKeyEnum
# from sqlalchemy.sql import quoted_name
import enum
class PromptKeyEnum(str, enum.Enum):
    rag_qa = "rag_qa"  # 知识问答
    tree_intent_match = "tree_intent_match"  # 意图识别
    tree_query_user = "tree_query_user"  # 反问
    tree_condition_judge = "tree_condition_judge"  # 条件判断
    tree_query_rewrite = "tree_query_rewrite"  # 问题改写
    tree_rag_qa = "tree_rag_qa"  # 文档答案生成
    tree_pre_condition_judge = "tree_pre_condition_judge"  # 条件预判断
    query_rewrite = "query_rewrite"  # 非知识树的query重写
    sensitive_check = "sensitive_check"  # 敏感检测
    tree_v2_intent_match = "tree_v2_intent_match"  # 知识树v2的意图识别
    search_guardrail = "search_guardrail"  # 搜索结果可用性检查
    qa_generate = "qa_generate"  # QA生成
    
    glm_evaluation_qd = "glm_evaluation_qd"  # 使用glm4进行结果标注 query & doc
    glm_evaluation_qad = "glm_evaluation_qad"  # 使用glm4进行结果标注 query & answer & doc
    glm_evaluation_qaa = "glm_evaluation_qaa"  # 使用glm4进行结果标注 query & answer & ref_answer
    abstract_generate = "abstract_generate"  # 摘要生成
    knowledge_simi_summary = "knowledge_simi_summary"  # 文本冲突总结

    email_point_extra = "email_point_extra"  # 邮件内容要点抽取
    email_auto_reply = "email_auto_reply"  # 邮件回复自动生成
    glm_outline_abstract = "glm_outline_abstract"  # 使用大模型生成大纲、摘要和推荐问题

class Prompt(Base):
    """ prompt表 """
    __tablename__ = "prompt"
    __table_args__ = {"schema": quoted_name("aico_rag", quote=True),"quote": True}
    
    id = Column("id", INTEGER, Identity(start=1, increment=1), primary_key=True, index=True, comment="ID", quote=True)
    project_id = Column("project_id", INTEGER, index=True, nullable=False, comment="项目关联ID", quote=True)
    key = Column("key", DbEnum(PromptKeyEnum), index=False, nullable=False, comment="prompt名称", quote=True)
    template = Column("template", CLOB, index=False, nullable=False, default="",  comment="prompt模版", quote=True)
    model = Column("model", String(255), index=True, nullable=False, default="glm-4", comment="模型", quote=True)
    model_params = Column("model_params", JSON, index=False, nullable=False, default={}, comment="模型参数", quote=True)
    system_prompt = Column("system_prompt", CLOB, index=False, nullable=False, default="", comment="系统prompt", quote=True)
    create_time = Column("create_time", DATETIME, nullable=False, index=False,
                         default=lambda: datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
                         comment="创建时间", quote=True)
    update_time = Column("update_time", DATETIME, nullable=False, index=False,
                         default=lambda: datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
                         comment="更新时间", quote=True)
    
# class PromptDmCompatible(Base):
#     """ prompt表 """
#     __tablename__ = "prompt"
#     __table_args__ =(
#         CheckConstraint(f"key IN ({','.join([f"'{item.value}'" for item in PromptKeyEnum])})", name="ck_prompt_key"), 
#         {"schema": quoted_name("aico_rag", quote=True),"quote": True})
    
#     id = Column("id", INTEGER, Identity(start=1, increment=1), primary_key=True, index=True, comment="ID", quote=True)
#     project_id = Column("project_id", INTEGER, index=True, nullable=False, comment="项目关联ID", quote=True)
#     key = Column("key", String(30), index=False, nullable=False, comment="prompt名称", quote=True)
#     template = Column("template", CLOB, index=False, nullable=False, default="",  comment="prompt模版", quote=True)
#     model = Column("model", String(255), index=True, nullable=False, default="glm-4", comment="模型", quote=True)
#     model_params = Column("model_params", JSON, index=False, nullable=False, default={}, comment="模型参数", quote=True)
#     system_prompt = Column("system_prompt", CLOB, index=False, nullable=False, default="", comment="系统prompt", quote=True)
#     create_time = Column("create_time", DATETIME, nullable=False, index=False,
#                          default=lambda: datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S"),
#                          comment="创建时间", quote=True)
#     update_time = Column("update_time", DATETIME, nullable=False, index=False,
#                          default=lambda: datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S"),
#                          comment="更新时间", quote=True)



if __name__ == "__main__":
    session = None
    try:
        # 创建会话
        session = SessionLocal()
        logger.info("\n=== 第二步：尝试插入原Prompt表（用DbEnum，达梦预期报错） ===")
        # 构造一个使用枚举的Prompt实例
        test_prompt = Prompt(
            project_id=1001,
            key=PromptKeyEnum.rag_qa,  # 使用枚举成员
            template="用户提问：{user_question}\n请基于知识库回答",
            model="glm-4",
            model_params={"temperature": 0.1, "max_tokens": 1024},
            system_prompt="你是专业的AI助手，仅基于提供的知识库回答问题"
        )
        session.add(test_prompt)
        session.commit()  # 达梦数据库会在此处报错：不支持ENUM类型
        logger.info("原Prompt表插入成功（若执行到这里，说明达梦版本支持ENUM，不符合预期）")
    except Exception as e:
        # 捕获达梦的ENUM不兼容错误，打印关键信息
        logger.error(f"\n=== 验证结果：达梦数据库不支持DbEnum枚举！ ===", exc_info=True)
        logger.error(f"错误核心原因：{str(e).split(chr(10))[0]}")  # 提取错误核心信息（如“无效的列类型: ENUM”）
        if session:
            session.rollback()  # 回滚事务，避免影响后续兼容版测试

        # 第三步：测试达梦兼容版表（VARCHAR+CHECK约束）- 预期成功
        logger.info("\n=== 第三步：测试达梦兼容版表（VARCHAR+CHECK约束，预期成功） ===")
        # try:
        #     # 构造兼容版实例（key用枚举的value，而非枚举成员）
        #     test_prompt_compatible = PromptDmCompatible(
        #         project_id=1001,
        #         key=PromptKeyEnum.rag_qa.value,  # 用枚举的字符串值，而非枚举成员
        #         template="用户提问：{user_question}\n请基于知识库回答",
        #         model="glm-4",
        #         model_params={"temperature": 0.1, "max_tokens": 1024},
        #         system_prompt="你是专业的AI助手，仅基于提供的知识库回答问题"
        #     )
        #     session.add(test_prompt_compatible)
        #     session.commit()
        #     logger.info("兼容版表插入成功！验证结论：达梦需用VARCHAR+CHECK约束替代DbEnum")

        #     # 第四步：查询验证插入结果
        #     queried_compatible = session.query(PromptDmCompatible).filter(
        #         PromptDmCompatible.project_id == 1001,
        #         PromptDmCompatible.key == PromptKeyEnum.rag_qa.value
        #     ).first()
        #     if queried_compatible:
        #         logger.info(f"\n查询到兼容版数据：")
        #         logger.info(f"key: {queried_compatible.key}（符合枚举约束）")
        #         logger.info(f"model: {queried_compatible.model}")
        #         logger.info(f"create_time: {queried_compatible.create_time}")

        # except Exception as e2:
        #     logger.error(f"兼容版表操作失败：{str(e2)}", exc_info=True)
        #     if session:
        #         session.rollback()

    finally:
        if session:
            session.close()
            logger.info("\n数据库会话已关闭")