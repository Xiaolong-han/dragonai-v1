"""Agent 工具模块"""

from .code import code_assist
from .document import read_pdf, read_word
from .image import edit_image, generate_image
from .multimodal import ocr_document, understand_image
from .rag import search_knowledge_base
from .translation import translate_text
from .web_search import web_search

# 所有工具列表 - 直接传递给 create_agent
# 注意：文件系统工具 (ls, read_file, write_file, edit_file, glob, grep)
# 由 FilesystemMiddleware 自动注入
ALL_TOOLS = [
    search_knowledge_base,
    web_search,
    ocr_document,
    understand_image,
    generate_image,
    edit_image,
    code_assist,
    translate_text,
    read_pdf,
    read_word,
]

__all__ = [
    "ALL_TOOLS",
    "code_assist",
    "edit_image",
    "generate_image",
    "ocr_document",
    "read_pdf",
    "read_word",
    "search_knowledge_base",
    "translate_text",
    "understand_image",
    "web_search",
]
