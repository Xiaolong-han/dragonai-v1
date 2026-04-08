"""多模态工具测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestUnderstandImage:
    """understand_image 工具测试"""

    @pytest.mark.asyncio
    async def test_understand_image_with_url(self):
        """测试使用 URL 理解图片"""
        from app.agents.tools.multimodal import understand_image

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(
            content="这是一张风景图片，包含蓝天、白云和绿色草地。"
        ))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model), \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}, {"type": "image_url", "image_url": {"url": "http://example.com/image.png"}}]

            result = await understand_image.ainvoke({
                "image_url": "http://example.com/image.png"
            })

        assert "风景图片" in result

    @pytest.mark.asyncio
    async def test_understand_image_with_local_path(self):
        """测试使用本地路径理解图片"""
        from app.agents.tools.multimodal import understand_image

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(
            content="这是一张截图，显示代码编辑器界面。"
        ))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model), \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,xxx"}}]

            result = await understand_image.ainvoke({
                "image_url": "images/screenshot.png"
            })

        assert "截图" in result

    @pytest.mark.asyncio
    async def test_understand_image_model_called_correctly(self):
        """测试模型被正确调用"""
        from app.agents.tools.multimodal import understand_image

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="描述"))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model) as mock_factory, \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}]

            await understand_image.ainvoke({"image_url": "test.png"})

            # 验证使用非 OCR 模式
            mock_factory.assert_called_once_with(is_ocr=False)


class TestOCRDocument:
    """ocr_document 工具测试"""

    @pytest.mark.asyncio
    async def test_ocr_document_success(self):
        """测试 OCR 文档成功"""
        from app.agents.tools.multimodal import ocr_document

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(
            content="识别出的文字内容：\n第一行\n第二行"
        ))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model), \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}, {"type": "image_url", "image_url": {"url": "http://example.com/doc.png"}}]

            result = await ocr_document.ainvoke({
                "image_url": "http://example.com/doc.png"
            })

        assert "识别" in result

    @pytest.mark.asyncio
    async def test_ocr_document_with_local_file(self):
        """测试 OCR 本地文件"""
        from app.agents.tools.multimodal import ocr_document

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(
            content="提取的文字内容"
        ))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model), \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}]

            result = await ocr_document.ainvoke({
                "image_url": "documents/scan.png"
            })

        assert "文字" in result

    @pytest.mark.asyncio
    async def test_ocr_document_uses_ocr_model(self):
        """测试 OCR 使用 OCR 模型"""
        from app.agents.tools.multimodal import ocr_document

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="OCR结果"))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model) as mock_factory, \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}]

            await ocr_document.ainvoke({"image_url": "test.png"})

            # 验证使用 OCR 模式
            mock_factory.assert_called_once_with(is_ocr=True)

    @pytest.mark.asyncio
    async def test_ocr_document_preserves_format(self):
        """测试 OCR 保持格式"""
        from app.agents.tools.multimodal import ocr_document

        # 模拟返回带格式的内容
        formatted_text = """标题
=====
正文内容
- 列表项1
- 列表项2"""
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content=formatted_text))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model), \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}]

            result = await ocr_document.ainvoke({"image_url": "test.png"})

        # 验证格式被保留
        assert "=====" in result
        assert "列表项" in result


class TestMultimodalErrorHandling:
    """多模态工具错误处理测试"""

    @pytest.mark.asyncio
    async def test_understand_image_model_error(self):
        """测试图片理解模型错误"""
        from app.agents.tools.multimodal import understand_image

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(side_effect=Exception("Model error"))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model), \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}]

            with pytest.raises(Exception):
                await understand_image.ainvoke({"image_url": "test.png"})

    @pytest.mark.asyncio
    async def test_ocr_document_model_error(self):
        """测试 OCR 模型错误"""
        from app.agents.tools.multimodal import ocr_document

        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(side_effect=Exception("OCR error"))

        with patch('app.agents.tools.multimodal.ModelFactory.get_vision_model', return_value=mock_model), \
             patch('app.agents.tools.multimodal.build_openai_image_content_async') as mock_build:
            mock_build.return_value = [{"type": "text", "text": "prompt"}]

            with pytest.raises(Exception):
                await ocr_document.ainvoke({"image_url": "test.png"})


class TestMultimodalToolDefinitions:
    """多模态工具定义测试"""

    def test_understand_image_tool_definition(self):
        """测试 understand_image 工具定义"""
        from app.agents.tools.multimodal import understand_image

        assert understand_image.name == "understand_image"
        assert "理解" in understand_image.description or "描述" in understand_image.description

    def test_ocr_document_tool_definition(self):
        """测试 ocr_document 工具定义"""
        from app.agents.tools.multimodal import ocr_document

        assert ocr_document.name == "ocr_document"
        assert "OCR" in ocr_document.description or "文字" in ocr_document.description

    def test_tools_have_proper_args(self):
        """测试工具有正确的参数定义"""
        from app.agents.tools.multimodal import understand_image, ocr_document

        # 检查参数
        understand_args = understand_image.args_schema.model_json_schema()
        assert "image_url" in understand_args.get("properties", {})

        ocr_args = ocr_document.args_schema.model_json_schema()
        assert "image_url" in ocr_args.get("properties", {})