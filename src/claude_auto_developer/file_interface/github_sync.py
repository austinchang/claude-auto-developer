#!/usr/bin/env python3
"""
GitHub Sync - GitHub 任務文件同步器
支援從 GitHub 倉庫定期同步 TASKS.md 文件，允許遠端編輯和協作
"""

import asyncio
import aiohttp
import base64
import hashlib
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import os

from .task_file_parser import TaskFileParser
from .progress_updater import ProgressUpdater

logger = logging.getLogger(__name__)

@dataclass
class GitHubConfig:
    """GitHub 配置"""
    token: str                          # GitHub Personal Access Token
    repo_owner: str                     # 倉庫擁有者
    repo_name: str                      # 倉庫名稱
    file_path: str = "TASKS.md"        # 文件在倉庫中的路徑
    branch: str = "main"               # 分支名稱
    sync_interval: int = 300           # 同步間隔（秒）
    local_file_path: str = "/home/tengjung_chang/TASKS.md"
    
    @classmethod
    def from_env(cls, local_file_path: Optional[str] = None) -> 'GitHubConfig':
        """從環境變數創建 GitHub 配置
        
        Args:
            local_file_path: 本地文件路徑，如果不提供則使用默認值
            
        Returns:
            GitHubConfig: GitHub 配置實例
            
        Raises:
            ValueError: 如果必要的環境變數未設置
        """
        # 讀取 GitHub Token
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            # 嘗試從 .git-credentials 讀取
            try:
                credentials_path = Path.home() / '.git-credentials'
                if credentials_path.exists():
                    with open(credentials_path, 'r') as f:
                        for line in f:
                            if 'github.com' in line:
                                # 格式: https://username:token@github.com
                                if ':' in line and '@github.com' in line:
                                    token = line.split(':')[2].split('@')[0].strip()
                                    break
            except Exception as e:
                logger.warning(f"無法從 .git-credentials 讀取 token: {e}")
        
        if not token:
            raise ValueError("GitHub token 未設置，請設置 GITHUB_TOKEN 環境變數或配置 .git-credentials")
        
        # 倉庫配置
        repo_owner = os.getenv('GITHUB_REPO_OWNER', 'austinchang')
        repo_name = os.getenv('GITHUB_REPO_NAME', 'claude-auto-developer-tasks')
        
        # 其他配置
        file_path = os.getenv('GITHUB_FILE_PATH', 'TASKS.md')
        branch = os.getenv('GITHUB_BRANCH', 'main')
        sync_interval = int(os.getenv('GITHUB_SYNC_INTERVAL', '300'))
        
        if local_file_path is None:
            local_file_path = os.getenv('LOCAL_TASKS_FILE', '/home/tengjung_chang/TASKS.md')
        
        return cls(
            token=token,
            repo_owner=repo_owner,
            repo_name=repo_name,
            file_path=file_path,
            branch=branch,
            sync_interval=sync_interval,
            local_file_path=local_file_path
        )

@dataclass
class SyncResult:
    """同步結果"""
    success: bool
    action: str                        # 'downloaded', 'uploaded', 'no_change', 'conflict'
    message: str
    local_hash: Optional[str] = None
    remote_hash: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class GitHubTaskSync:
    """GitHub 任務文件同步器"""
    
    def __init__(self, config: GitHubConfig):
        """
        初始化 GitHub 同步器
        
        Args:
            config: GitHub 配置
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_syncing = False
        self.sync_task: Optional[asyncio.Task] = None
        
        # 同步狀態
        self.last_sync: Optional[datetime] = None
        self.last_remote_sha: Optional[str] = None
        self.last_local_hash: Optional[str] = None
        self.sync_history: List[SyncResult] = []
        
        # 組件
        self.parser = TaskFileParser(self.config.local_file_path)
        self.updater = ProgressUpdater(self.config.local_file_path)
        
        # 統計
        self.stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'downloads': 0,
            'uploads': 0,
            'conflicts': 0,
            'last_error': None
        }
    
    async def __aenter__(self):
        """異步上下文管理器進入"""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        await self._close_session()
    
    async def _create_session(self):
        """創建 HTTP 會話"""
        if not self.session:
            headers = {
                'Authorization': f'token {self.config.token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Claude-Auto-Developer/1.0'
            }
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def _close_session(self):
        """關閉 HTTP 會話"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def start_auto_sync(self):
        """開始自動同步"""
        if self.is_syncing:
            logger.warning("GitHub 同步已在運行中")
            return
        
        logger.info(f"開始 GitHub 同步 - 間隔: {self.config.sync_interval} 秒")
        self.is_syncing = True
        self.sync_task = asyncio.create_task(self._sync_loop())
    
    def stop_auto_sync(self):
        """停止自動同步"""
        if not self.is_syncing:
            return
        
        self.is_syncing = False
        if self.sync_task and not self.sync_task.done():
            self.sync_task.cancel()
        
        logger.info("已停止 GitHub 同步")
    
    async def _sync_loop(self):
        """同步循環"""
        await self._create_session()
        
        try:
            while self.is_syncing:
                try:
                    await self.sync_once()
                    await asyncio.sleep(self.config.sync_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"同步過程中發生錯誤: {str(e)}")
                    self.stats['last_error'] = str(e)
                    await asyncio.sleep(60)  # 錯誤後等待 1 分鐘再重試
        
        finally:
            await self._close_session()
    
    async def sync_once(self) -> SyncResult:
        """執行一次同步"""
        self.stats['total_syncs'] += 1
        
        try:
            logger.debug("開始同步檢查...")
            
            # 獲取遠端文件資訊
            remote_info = await self._get_remote_file_info()
            if not remote_info:
                return SyncResult(
                    success=False,
                    action='error',
                    message='無法獲取遠端文件資訊'
                )
            
            # 計算本地文件雜湊
            local_hash = self._calculate_local_hash()
            
            # 比較版本決定同步方向
            sync_result = await self._determine_sync_action(remote_info, local_hash)
            
            if sync_result.success:
                self.stats['successful_syncs'] += 1
                self.last_sync = datetime.now()
                
                # 更新狀態追蹤
                if sync_result.action == 'downloaded':
                    self.stats['downloads'] += 1
                    self.last_remote_sha = remote_info['sha']
                elif sync_result.action == 'uploaded':
                    self.stats['uploads'] += 1
                    self.last_local_hash = local_hash
            
            # 記錄同步歷史
            self.sync_history.append(sync_result)
            if len(self.sync_history) > 100:  # 只保留最近 100 次記錄
                self.sync_history.pop(0)
            
            return sync_result
            
        except Exception as e:
            error_msg = f"同步失敗: {str(e)}"
            logger.error(error_msg)
            
            result = SyncResult(
                success=False,
                action='error',
                message=error_msg
            )
            self.sync_history.append(result)
            return result
    
    async def _get_remote_file_info(self) -> Optional[Dict[str, Any]]:
        """獲取遠端文件資訊"""
        url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}/contents/{self.config.file_path}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 404:
                    logger.info("遠端文件不存在，將創建新文件")
                    return None
                elif response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"獲取遠端文件失敗: {response.status} - {error_text}")
                    return None
        
        except Exception as e:
            logger.error(f"請求遠端文件資訊失敗: {str(e)}")
            return None
    
    def _calculate_local_hash(self) -> Optional[str]:
        """計算本地文件內容雜湊"""
        try:
            if not Path(self.config.local_file_path).exists():
                return None
            
            with open(self.config.local_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        except Exception as e:
            logger.error(f"計算本地文件雜湊失敗: {str(e)}")
            return None
    
    async def _determine_sync_action(self, 
                                   remote_info: Optional[Dict[str, Any]], 
                                   local_hash: Optional[str]) -> SyncResult:
        """決定同步動作"""
        
        # 遠端文件不存在 - 上傳本地文件
        if not remote_info:
            if local_hash:
                return await self._upload_local_file()
            else:
                return SyncResult(
                    success=True,
                    action='no_change',
                    message='本地和遠端文件都不存在'
                )
        
        # 本地文件不存在 - 下載遠端文件
        if not local_hash:
            return await self._download_remote_file(remote_info)
        
        # 比較文件內容
        remote_content = base64.b64decode(remote_info['content']).decode('utf-8')
        remote_hash = hashlib.sha256(remote_content.encode('utf-8')).hexdigest()
        
        # 內容相同 - 無需同步
        if local_hash == remote_hash:
            return SyncResult(
                success=True,
                action='no_change',
                message='本地和遠端文件內容相同',
                local_hash=local_hash,
                remote_hash=remote_hash
            )
        
        # 內容不同 - 根據修改時間決定方向
        local_mtime = Path(self.config.local_file_path).stat().st_mtime
        local_modified = datetime.fromtimestamp(local_mtime)
        
        remote_modified = datetime.fromisoformat(
            remote_info['commit']['author']['date'].replace('Z', '+00:00')
        ).replace(tzinfo=None)
        
        # 本地文件更新 - 上傳
        if local_modified > remote_modified:
            return await self._upload_local_file(remote_info['sha'])
        
        # 遠端文件更新 - 下載
        else:
            return await self._download_remote_file(remote_info)
    
    async def _download_remote_file(self, remote_info: Dict[str, Any]) -> SyncResult:
        """下載遠端文件"""
        try:
            # 備份本地文件
            await self._backup_local_file()
            
            # 解碼遠端內容
            remote_content = base64.b64decode(remote_info['content']).decode('utf-8')
            
            # 寫入本地文件
            with open(self.config.local_file_path, 'w', encoding='utf-8') as f:
                f.write(remote_content)
            
            logger.info("已從 GitHub 下載最新版本的任務文件")
            
            return SyncResult(
                success=True,
                action='downloaded',
                message=f"已下載遠端文件 (SHA: {remote_info['sha'][:8]})",
                remote_hash=hashlib.sha256(remote_content.encode('utf-8')).hexdigest()
            )
        
        except Exception as e:
            error_msg = f"下載遠端文件失敗: {str(e)}"
            logger.error(error_msg)
            return SyncResult(success=False, action='error', message=error_msg)
    
    async def _upload_local_file(self, remote_sha: Optional[str] = None) -> SyncResult:
        """上傳本地文件"""
        try:
            # 讀取本地文件
            with open(self.config.local_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Base64 編碼
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # 準備上傳數據
            upload_data = {
                'message': f'更新任務文件 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'content': encoded_content,
                'branch': self.config.branch
            }
            
            # 如果遠端文件存在，需要提供 SHA
            if remote_sha:
                upload_data['sha'] = remote_sha
            
            # 上傳文件
            url = f"https://api.github.com/repos/{self.config.repo_owner}/{self.config.repo_name}/contents/{self.config.file_path}"
            
            async with self.session.put(url, json=upload_data) as response:
                if response.status in [200, 201]:
                    result_data = await response.json()
                    logger.info("已將本地文件上傳至 GitHub")
                    
                    return SyncResult(
                        success=True,
                        action='uploaded',
                        message=f"已上傳本地文件 (SHA: {result_data['content']['sha'][:8]})",
                        local_hash=hashlib.sha256(content.encode('utf-8')).hexdigest()
                    )
                else:
                    error_text = await response.text()
                    error_msg = f"上傳失敗: {response.status} - {error_text}"
                    logger.error(error_msg)
                    return SyncResult(success=False, action='error', message=error_msg)
        
        except Exception as e:
            error_msg = f"上傳本地文件失敗: {str(e)}"
            logger.error(error_msg)
            return SyncResult(success=False, action='error', message=error_msg)
    
    async def _backup_local_file(self):
        """備份本地文件"""
        if not Path(self.config.local_file_path).exists():
            return
        
        try:
            backup_dir = Path(self.config.local_file_path).parent / '.github_sync_backups'
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"TASKS_backup_{timestamp}.md"
            
            import shutil
            shutil.copy2(self.config.local_file_path, backup_file)
            
            # 清理舊備份（保留最新 10 個）
            backup_files = list(backup_dir.glob("TASKS_backup_*.md"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for old_backup in backup_files[10:]:
                old_backup.unlink()
            
            logger.debug(f"已創建備份: {backup_file}")
        
        except Exception as e:
            logger.warning(f"創建備份失敗: {str(e)}")
    
    async def force_upload(self) -> SyncResult:
        """強制上傳本地文件（覆蓋遠端）"""
        logger.info("執行強制上傳...")
        
        remote_info = await self._get_remote_file_info()
        remote_sha = remote_info['sha'] if remote_info else None
        
        return await self._upload_local_file(remote_sha)
    
    async def force_download(self) -> SyncResult:
        """強制下載遠端文件（覆蓋本地）"""
        logger.info("執行強制下載...")
        
        remote_info = await self._get_remote_file_info()
        if not remote_info:
            return SyncResult(
                success=False,
                action='error',
                message='遠端文件不存在，無法下載'
            )
        
        return await self._download_remote_file(remote_info)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """獲取同步狀態"""
        return {
            'is_syncing': self.is_syncing,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'config': {
                'repo': f"{self.config.repo_owner}/{self.config.repo_name}",
                'file_path': self.config.file_path,
                'branch': self.config.branch,
                'sync_interval': self.config.sync_interval
            },
            'stats': self.stats.copy(),
            'recent_syncs': [
                {
                    'action': sync.action,
                    'success': sync.success,
                    'message': sync.message,
                    'timestamp': sync.timestamp.isoformat()
                }
                for sync in self.sync_history[-5:]  # 最近 5 次
            ]
        }
    
    @classmethod
    def from_env(cls, local_file_path: Optional[str] = None) -> 'GitHubTaskSync':
        """從環境變數創建同步器"""
        config = GitHubConfig(
            token=os.getenv('GITHUB_TOKEN', ''),
            repo_owner=os.getenv('GITHUB_REPO_OWNER', ''),
            repo_name=os.getenv('GITHUB_REPO_NAME', ''),
            file_path=os.getenv('GITHUB_TASKS_FILE', 'TASKS.md'),
            branch=os.getenv('GITHUB_BRANCH', 'main'),
            sync_interval=int(os.getenv('GITHUB_SYNC_INTERVAL', '300')),
            local_file_path=local_file_path or '/home/tengjung_chang/TASKS.md'
        )
        
        return cls(config)
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """驗證配置"""
        errors = []
        
        if not self.config.token:
            errors.append("GitHub token 未設定")
        
        if not self.config.repo_owner:
            errors.append("倉庫擁有者未設定")
        
        if not self.config.repo_name:
            errors.append("倉庫名稱未設定")
        
        if self.config.sync_interval < 60:
            errors.append("同步間隔不能少於 60 秒")
        
        return len(errors) == 0, errors

# 使用範例
async def main():
    """測試 GitHub 同步功能"""
    logging.basicConfig(level=logging.INFO)
    
    # 創建配置
    config = GitHubConfig(
        token="your_github_token",
        repo_owner="austinchang",
        repo_name="claude-auto-developer-tasks",
        file_path="TASKS.md",
        sync_interval=60  # 1 分鐘同步一次（測試用）
    )
    
    # 創建同步器
    async with GitHubTaskSync(config) as sync:
        # 驗證配置
        valid, errors = sync.validate_config()
        if not valid:
            print(f"配置錯誤: {errors}")
            return
        
        # 執行一次同步
        result = await sync.sync_once()
        print(f"同步結果: {result.action} - {result.message}")
        
        # 開始自動同步
        sync.start_auto_sync()
        
        try:
            # 運行 5 分鐘
            await asyncio.sleep(300)
        except KeyboardInterrupt:
            print("停止同步...")
        finally:
            sync.stop_auto_sync()
        
        # 顯示狀態
        status = sync.get_sync_status()
        print(f"最終狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())