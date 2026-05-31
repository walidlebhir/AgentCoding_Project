from springforge_cli.core.agent import Agent
from springforge_cli.utils.logger import info, success, error, step, header


def handle(agent: Agent, feature: str, project_path: str | None = None) -> bool:
    header("SPRINGFORGE — Add Feature")
    info(f"Feature : {feature}")
    if project_path:
        info(f"Project : {project_path}")
    step("Analyzing project...")
    step("Integrating new feature...")
    result = agent.add(feature, project_path)
    if result:
        success(f"Feature '{feature}' added successfully")
    else:
        error("Failed to add feature")
    return result
