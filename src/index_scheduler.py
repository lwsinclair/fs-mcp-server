import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict
import logging

from .codebase_indexer import CodebaseIndexer

logger = logging.getLogger(__name__)

class IndexScheduler:
    """索引调度器 - 定时更新代码库索引"""
    
    def __init__(self, indexer: Optional[CodebaseIndexer] = None):
        """初始化调度器"""
        self.indexer = indexer or CodebaseIndexer()
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        self.last_index_time: Optional[datetime] = None
        self.index_interval_hours = 1  # 默认6小时索引一次
        self.callbacks: Dict[str, Callable] = {}
        
        # 设置默认调度
        self._setup_default_schedule()
    
    def _setup_default_schedule(self):
        """设置默认的调度计划"""
        # 每6小时重建索引
        schedule.every(self.index_interval_hours).hours.do(self._sync_scheduled_rebuild)
        
        # 每天凌晨2点强制重建索引（数据库维护）
        schedule.every().day.at("02:00").do(self._sync_scheduled_full_rebuild)
        
        logger.info(f"设置默认调度: 每{self.index_interval_hours}小时重建索引，每天凌晨2点强制重建")
    
    def set_index_interval(self, hours: int):
        """设置索引间隔时间"""
        if hours < 1:
            raise ValueError("索引间隔不能小于1小时")
        
        # 清除现有的按小时调度
        schedule.clear('hourly-rebuild')
        
        # 设置新的调度
        schedule.every(hours).hours.do(self._sync_scheduled_rebuild).tag('hourly-rebuild')
        self.index_interval_hours = hours
        
        logger.info(f"更新索引间隔为: {hours}小时")
    
    def add_callback(self, event: str, callback: Callable):
        """
        添加事件回调
        
        支持的事件:
        - 'index_start': 索引开始
        - 'index_complete': 索引完成
        - 'index_error': 索引出错
        """
        if event not in ['index_start', 'index_complete', 'index_error']:
            raise ValueError(f"不支持的事件类型: {event}")
        
        self.callbacks[event] = callback
        logger.info(f"添加回调函数: {event}")
    
    def _call_callback(self, event: str, *args, **kwargs):
        """调用回调函数"""
        callback = self.callbacks.get(event)
        if callback:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"回调函数执行失败 {event}: {e}")
    
    def _sync_scheduled_rebuild(self):
        """同步包装器 - 定时重建索引"""
        try:
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._scheduled_rebuild())
        except Exception as e:
            logger.error(f"同步调度重建失败: {e}")
        finally:
            loop.close()
    
    def _sync_scheduled_full_rebuild(self):
        """同步包装器 - 定时完整重建索引"""
        try:
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._scheduled_full_rebuild())
        except Exception as e:
            logger.error(f"同步调度完整重建失败: {e}")
        finally:
            loop.close()
    
    async def _scheduled_rebuild(self):
        """定时重建索引（增量更新）"""
        try:
            self._call_callback('index_start', 'scheduled')
            
            logger.info("开始定时索引重建...")
            start_time = datetime.now()
            
            # 执行重建
            result = await self.indexer.rebuild_index()
            
            # 更新最后索引时间
            self.last_index_time = datetime.now()
            
            duration = (self.last_index_time - start_time).total_seconds()
            
            logger.info(f"定时索引重建完成: {result}, 耗时: {duration:.2f}秒")
            
            self._call_callback('index_complete', 'scheduled', result)
            
        except Exception as e:
            logger.error(f"定时索引重建失败: {e}")
            self._call_callback('index_error', 'scheduled', e)
    
    async def _scheduled_full_rebuild(self):
        """定时完整重建索引（清理数据库）"""
        try:
            self._call_callback('index_start', 'full_rebuild')
            
            logger.info("开始完整索引重建...")
            start_time = datetime.now()
            
            # 执行完整重建
            result = await self.indexer.rebuild_index()
            
            # 更新最后索引时间
            self.last_index_time = datetime.now()
            
            duration = (self.last_index_time - start_time).total_seconds()
            
            logger.info(f"完整索引重建完成: {result}, 耗时: {duration:.2f}秒")
            
            self._call_callback('index_complete', 'full_rebuild', result)
            
        except Exception as e:
            logger.error(f"完整索引重建失败: {e}")
            self._call_callback('index_error', 'full_rebuild', e)
    
    def _run_scheduler(self):
        """运行调度器循环"""
        logger.info("索引调度器启动")
        
        while self.running:
            try:
                # 运行待执行的任务
                schedule.run_pending()
                
                # 休眠1分钟
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"调度器运行错误: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
        
        logger.info("索引调度器停止")
    
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return
        
        self.running = True
        
        # 启动调度器线程
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler,
            daemon=True,
            name="IndexScheduler"
        )
        self.scheduler_thread.start()
        
        logger.info("索引调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            logger.warning("调度器未在运行")
            return
        
        self.running = False
        
        # 等待线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("索引调度器已停止")
    
    async def manual_rebuild(self) -> Dict:
        """手动触发索引重建"""
        try:
            self._call_callback('index_start', 'manual')
            
            logger.info("手动触发索引重建...")
            start_time = datetime.now()
            
            result = await self.indexer.rebuild_index()
            
            self.last_index_time = datetime.now()
            duration = (self.last_index_time - start_time).total_seconds()
            
            logger.info(f"手动索引重建完成: {result}, 耗时: {duration:.2f}秒")
            
            self._call_callback('index_complete', 'manual', result)
            
            return result
            
        except Exception as e:
            logger.error(f"手动索引重建失败: {e}")
            self._call_callback('index_error', 'manual', e)
            raise
    
    def get_next_run_time(self) -> Optional[datetime]:
        """获取下次运行时间"""
        try:
            next_run = schedule.next_run()
            if next_run:
                return next_run
        except Exception:
            pass
        return None
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        next_run = self.get_next_run_time()
        
        return {
            'running': self.running,
            'last_index_time': self.last_index_time.isoformat() if self.last_index_time else None,
            'next_run_time': next_run.isoformat() if next_run else None,
            'index_interval_hours': self.index_interval_hours,
            'scheduled_jobs': len(schedule.jobs),
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }
    
    def force_index_if_needed(self, max_age_hours: int = 24) -> bool:
        """
        如果索引太旧则强制重建
        
        Args:
            max_age_hours: 最大允许的索引年龄（小时）
            
        Returns:
            是否触发了重建
        """
        if not self.last_index_time:
            # 没有索引记录，需要立即重建
            logger.info("未找到索引记录，准备立即重建")
            return True
        
        age = datetime.now() - self.last_index_time
        if age.total_seconds() > max_age_hours * 3600:
            logger.info(f"索引过旧 ({age.total_seconds()/3600:.1f}小时)，准备重建")
            return True
        
        return False 