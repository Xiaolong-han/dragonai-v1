
import pytest
from datetime import timedelta
from unittest.mock import patch
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    generate_file_signature,
    verify_file_signature,
    generate_signed_url,
)


class TestSecurity:
    def test_password_hashing(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_success(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert token is not None
        assert len(token) > 0

    def test_create_access_token_with_expiration(self):
        data = {"sub": "testuser"}
        expires = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires)
        assert token is not None

    def test_decode_access_token(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "testuser"

    def test_decode_access_token_invalid(self):
        token = "invalid.token.here"
        decoded = decode_access_token(token)
        assert decoded is None


class TestFileSignature:
    """文件签名功能测试"""

    def test_generate_file_signature(self):
        """测试签名生成"""
        relative_path = "images/test.png"
        expires_timestamp = 9999999999
        
        signature = generate_file_signature(relative_path, expires_timestamp)
        
        assert signature is not None
        assert len(signature) > 0
        assert isinstance(signature, str)

    def test_verify_file_signature_valid(self):
        """测试有效签名验证"""
        relative_path = "images/test.png"
        expires_timestamp = 9999999999
        
        signature = generate_file_signature(relative_path, expires_timestamp)
        is_valid = verify_file_signature(relative_path, expires_timestamp, signature)
        
        assert is_valid is True

    def test_verify_file_signature_expired(self):
        """测试过期签名验证"""
        relative_path = "images/test.png"
        expires_timestamp = 1000000000
        
        signature = generate_file_signature(relative_path, expires_timestamp)
        is_valid = verify_file_signature(relative_path, expires_timestamp, signature)
        
        assert is_valid is False

    def test_verify_file_signature_invalid(self):
        """测试无效签名验证"""
        relative_path = "images/test.png"
        expires_timestamp = 9999999999
        
        is_valid = verify_file_signature(relative_path, expires_timestamp, "invalid_signature")
        
        assert is_valid is False

    def test_verify_file_signature_path_traversal(self):
        """测试路径遍历攻击防护"""
        relative_path = "../../../etc/passwd"
        expires_timestamp = 9999999999
        
        signature = generate_file_signature(relative_path, expires_timestamp)
        is_valid = verify_file_signature(relative_path, expires_timestamp, signature)
        
        assert is_valid is False

    def test_generate_signed_url_valid_path(self):
        """测试生成有效路径的签名URL"""
        relative_path = "images/test.png"
        
        with patch('app.storage.sandbox.FileSandbox.is_safe_path', return_value=True):
            url = generate_signed_url(relative_path)
        
        assert url is not None
        assert "/api/v1/files/serve/" in url
        assert "expires=" in url
        assert "signature=" in url

    def test_generate_signed_url_path_traversal(self):
        """测试路径遍历攻击防护"""
        relative_path = "../../../etc/passwd"
        
        with patch('app.storage.sandbox.FileSandbox.is_safe_path', return_value=False):
            with pytest.raises(ValueError, match="Access denied"):
                generate_signed_url(relative_path)

    def test_generate_signed_url_absolute_path_outside_sandbox(self):
        """测试绝对路径在沙箱外"""
        relative_path = "/etc/passwd"
        
        with patch('app.storage.sandbox.FileSandbox.is_safe_path', return_value=False):
            with pytest.raises(ValueError, match="Access denied"):
                generate_signed_url(relative_path)
