"""自定义技能中间件

继承自 DeepAgents 的 SkillsMiddleware，添加自定义系统提示模板支持。
"""

from deepagents.middleware.skills import SkillsMiddleware
from deepagents.backends.protocol import BACKEND_TYPES


class CustomSkillsMiddleware(SkillsMiddleware):
    """支持自定义系统提示模板的 SkillsMiddleware

    继承自 SkillsMiddleware，添加 system_prompt_template 参数支持，
    允许使用自定义的系统提示模板（如中文版本）。

    Example:
        ```python
        from app.agents.middleware.skills import CustomSkillsMiddleware
        from app.agents.prompts import SKILLS_SYSTEM_PROMPT_CN

        middleware = CustomSkillsMiddleware(
            backend=backend,
            sources=["/skills/"],
            system_prompt_template=SKILLS_SYSTEM_PROMPT_CN,
        )
        ```

    Args:
        backend: Backend instance for file operations
        sources: List of skill source paths
        system_prompt_template: Optional custom system prompt template.
            If not provided, uses the default SKILLS_SYSTEM_PROMPT.
    """

    def __init__(
        self,
        *,
        backend: BACKEND_TYPES,
        sources: list[str],
        system_prompt_template: str | None = None,
    ) -> None:
        """Initialize the custom skills middleware.

        Args:
            backend: Backend instance or factory function
            sources: List of skill source paths
            system_prompt_template: Custom system prompt template with
                {skills_locations} and {skills_list} placeholders
        """
        # 调用父类初始化
        super().__init__(backend=backend, sources=sources)

        # 如果提供了自定义模板，覆盖父类设置的模板
        if system_prompt_template is not None:
            self.system_prompt_template = system_prompt_template