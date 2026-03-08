from app.bootstrap.bt_run_container import build_bt_run_agent


def main():

    agent = build_bt_run_agent()

    result = agent.execute()

    if result.is_ok:
        print("Report created:", result.value)
    else:
        print("Agent failed:", result.error)


if __name__ == "__main__":
    main()