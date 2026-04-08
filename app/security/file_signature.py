"""文件签名功能"""

import base64
import hashlib
import hmac
import logging
import urllib.parse
from datetime import UTC, datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)


def generate_file_signature(relative_path: str, expires_timestamp: int) -> str:
    """生成文件访问签名

    Args:
        relative_path: 文件相对路径
        expires_timestamp: 过期时间戳

    Returns:
        签名字符串
    """
    message = f"{relative_path}:{expires_timestamp}"
    signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")


def verify_file_signature(relative_path: str, expires_timestamp: int, signature: str) -> bool:
    """验证文件访问签名

    Args:
        relative_path: 文件相对路径
        expires_timestamp: 过期时间戳
        signature: 签名字符串

    Returns:
        签名是否有效
    """
    from app.storage.sandbox import FileSandbox

    if not FileSandbox.is_safe_path(relative_path):
        logger.warning(f"[SECURITY] Path traversal attempt blocked: {relative_path}")
        return False

    expected_signature = generate_file_signature(relative_path, expires_timestamp)
    if not hmac.compare_digest(expected_signature, signature):
        return False

    return not datetime.now(UTC).timestamp() > expires_timestamp


def generate_signed_url(relative_path: str, expires_in_seconds: int = 3600) -> str:
    """生成带签名的文件访问URL

    Args:
        relative_path: 文件相对路径 (必须在沙箱内)
        expires_in_seconds: 过期时间（秒），默认1小时

    Returns:
        带签名的相对URL路径

    Raises:
        ValueError: 路径不在沙箱内
    """
    from app.storage.sandbox import FileSandbox

    if not FileSandbox.is_safe_path(relative_path):
        logger.warning(f"[SECURITY] Blocked signed URL generation for unsafe path: {relative_path}")
        raise ValueError("Access denied: path outside sandbox")

    expires_timestamp = int((datetime.now(UTC) + timedelta(seconds=expires_in_seconds)).timestamp())
    signature = generate_file_signature(relative_path, expires_timestamp)

    encoded_path = urllib.parse.quote(relative_path, safe="")
    return f"/api/v1/files/serve/{encoded_path}?expires={expires_timestamp}&signature={signature}"
