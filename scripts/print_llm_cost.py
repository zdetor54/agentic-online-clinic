from loguru import logger

from src.core.llm_logger import get_llm_logger


def main() -> None:
    llm_logger = get_llm_logger()
    total_cost = llm_logger.get_total_cost()
    logger.info("-" * 31)
    logger.info(f"Total LLM cost: ${total_cost:.3f} USD")
    logger.info("-" * 30 + "\n")

    breakdown = llm_logger.get_cost_breakdown()
    if not breakdown:
        logger.warning("No cost breakdown available.")
        return

    logger.info("Cost breakdown by project, date, hour, and model:")
    for project_name in breakdown:
        logger.info(f"Project: {project_name}")
        for date in sorted(breakdown[project_name]):
            logger.info(f"  Date: {date}")
            for model in sorted(breakdown[project_name][date]):
                cost = breakdown[project_name][date][model]
                logger.info(f"      Model: {model:20s}  Cost: ${cost:.3f}")

    logger.info("\n")


if __name__ == "__main__":
    main()
