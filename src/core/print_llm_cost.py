from src.core.llm_logger import get_llm_logger


def main() -> None:
    logger = get_llm_logger()
    total_cost = logger.get_total_cost()
    print(f"Total LLM cost: ${total_cost:.3f} USD\n")

    breakdown = logger.get_cost_breakdown()
    if not breakdown:
        print("No cost breakdown available.")
        return

    print("Cost breakdown by date, hour, and model:")
    for date in sorted(breakdown):
        print(f"Date: {date}")
        for hour in sorted(breakdown[date]):
            print(f"  Hour: {hour}")
            for model in sorted(breakdown[date][hour]):
                cost = breakdown[date][hour][model]
                print(f"    Model: {model:20s}  Cost: ${cost:.3f}")


if __name__ == "__main__":
    main()
