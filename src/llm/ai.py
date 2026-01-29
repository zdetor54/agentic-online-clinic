from loguru import logger


def do_ai(prompt: str, model_name: str) -> str:
    """Dummy generate AI response"""

    if "error" in prompt.lower():
        logger.error(f"Error detected in prompt: {prompt}")
        return "Error: Invalid prompt."

    logger.success(f"User submitted prompt: {prompt}")
    response = f"AI response to '{prompt}' using model '{model_name}'"
    logger.info(response)
    return response
