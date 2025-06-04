import sys
import time
from typing import Optional

class ProgressBar:
    """控制台进度条"""
    
    def __init__(self, total: int, description: str = "进度", width: int = 50):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()
        
    def update(self, count: int = 1, description: Optional[str] = None):
        """更新进度"""
        self.current = min(self.current + count, self.total)
        
        if description:
            self.description = description
            
        self._display()
    
    def set_progress(self, current: int, description: Optional[str] = None):
        """设置当前进度"""
        self.current = min(current, self.total)
        
        if description:
            self.description = description
            
        self._display()
    
    def _display(self):
        """显示进度条"""
        if self.total == 0:
            percent = 0
        else:
            percent = self.current / self.total
        
        # 计算进度条长度
        filled_length = int(self.width * percent)
        bar = '█' * filled_length + '░' * (self.width - filled_length)
        
        # 计算耗时和预估剩余时间
        elapsed_time = time.time() - self.start_time
        if self.current > 0 and percent > 0:
            eta = elapsed_time / percent - elapsed_time
            eta_str = f"{eta:.1f}s" if eta < 60 else f"{eta/60:.1f}m"
        else:
            eta_str = "计算中..."
        
        # 格式化输出
        progress_text = (
            f"\r{self.description}: |{bar}| "
            f"{self.current}/{self.total} "
            f"({percent:.1%}) "
            f"用时:{elapsed_time:.1f}s "
            f"剩余:{eta_str}"
        )
        
        # 输出进度条（不换行）
        sys.stdout.write(progress_text)
        sys.stdout.flush()
        
        # 完成时换行
        if self.current >= self.total:
            sys.stdout.write("\n")
            sys.stdout.flush()
    
    def finish(self, description: Optional[str] = None):
        """完成进度条"""
        self.current = self.total
        if description:
            self.description = description
        self._display()

class SimpleSpinner:
    """简单的旋转进度指示器"""
    
    def __init__(self, description: str = "处理中"):
        self.description = description
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_char = 0
        self.start_time = time.time()
    
    def update(self, description: Optional[str] = None):
        """更新旋转指示器"""
        if description:
            self.description = description
        
        elapsed = time.time() - self.start_time
        char = self.spinner_chars[self.current_char % len(self.spinner_chars)]
        
        sys.stdout.write(f"\r{char} {self.description} ({elapsed:.1f}s)")
        sys.stdout.flush()
        
        self.current_char += 1
    
    def finish(self, description: Optional[str] = None):
        """完成指示器"""
        if description:
            self.description = description
        
        elapsed = time.time() - self.start_time
        sys.stdout.write(f"\r✅ {self.description} ({elapsed:.1f}s)\n")
        sys.stdout.flush() 