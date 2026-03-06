"""文件沙箱测试"""

import pytest
from pathlib import Path
from unittest.mock import patch

from app.storage.sandbox import FileSandbox


class TestFileSandbox:
    """FileSandbox 类测试"""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """创建临时存储目录"""
        storage = tmp_path / "storage"
        storage.mkdir()
        return storage
    
    def test_sandbox_dir_resolution(self):
        """测试沙箱目录解析"""
        sandbox_dir = FileSandbox.get_sandbox_dir()
        assert sandbox_dir is not None
        assert sandbox_dir.is_absolute()

    def test_validate_path_relative(self, temp_storage):
        """测试相对路径验证"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            result = FileSandbox.validate_path("test.txt")
            assert result.is_absolute()
            assert str(temp_storage) in str(result)

    def test_validate_path_with_leading_slash(self, temp_storage):
        """测试带前导斜杠的路径"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            result = FileSandbox.validate_path("/test.txt")
            assert result.is_absolute()
            assert str(temp_storage) in str(result)

    def test_validate_path_traversal_attack(self, temp_storage):
        """测试路径遍历攻击防护"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError, match="outside sandbox"):
                FileSandbox.validate_path("../../../etc/passwd")

    def test_validate_path_absolute_outside_sandbox(self, temp_storage):
        """测试绝对路径在沙箱外"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with patch.object(FileSandbox, '_is_subpath', return_value=False):
                with pytest.raises(PermissionError, match="outside sandbox"):
                    FileSandbox.validate_path("/etc/passwd")

    def test_validate_path_blocked_pattern_env(self, temp_storage):
        """测试阻止 .env 文件"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError, match="blocked pattern"):
                FileSandbox.validate_path(".env")

    def test_validate_path_blocked_pattern_ssh_key(self, temp_storage):
        """测试阻止 SSH 密钥文件"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError, match="blocked pattern"):
                FileSandbox.validate_path("id_rsa")

    def test_validate_path_for_write_allowed_extension(self, temp_storage):
        """测试允许的文件扩展名"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            result = FileSandbox.validate_path_for_write("test.txt")
            assert result.is_absolute()

    def test_validate_path_for_write_blocked_extension(self, temp_storage):
        """测试阻止的危险扩展名"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError, match="not allowed"):
                FileSandbox.validate_path_for_write("test.exe")

    def test_is_safe_path_valid(self, temp_storage):
        """测试安全路径检查"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            assert FileSandbox.is_safe_path("test.txt") is True

    def test_is_safe_path_invalid(self, temp_storage):
        """测试不安全路径检查"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            assert FileSandbox.is_safe_path("../../../etc/passwd") is False

    def test_is_allowed_extension(self):
        """测试扩展名检查"""
        assert FileSandbox.is_allowed_extension("test.txt") is True
        assert FileSandbox.is_allowed_extension("test.exe") is False
        assert FileSandbox.is_allowed_extension("test.py") is True

    def test_to_virtual_path(self, temp_storage):
        """测试转换为虚拟路径"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            file_path = temp_storage / "images" / "test.png"
            virtual = FileSandbox.to_virtual_path(file_path)
            assert virtual.startswith("/storage/")

    def test_to_virtual_path_outside_sandbox(self):
        """测试沙箱外路径转换"""
        file_path = Path("F:/etc/passwd")
        with patch.object(FileSandbox, '_is_subpath', return_value=False):
            virtual = FileSandbox.to_virtual_path(file_path)
            assert "passwd" in virtual
