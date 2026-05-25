import argparse
from scripts.state_engine import StateEngine
from scripts.run_m2m import run_demo
from scripts.input_flow import run_input_flow


def main() -> None:
    parser = argparse.ArgumentParser(description="KRXA local execution engine")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "reset", "advance", "run-m2m", "input-flow", "recover"])
    parser.add_argument("--message", default="안녕하세요. 말대말 로컬 실행 테스트입니다.")
    args = parser.parse_args()

    engine = StateEngine()

    if args.command == "status":
        print("KRXA EXEC ENGINE: READY")
        print(f"STATE: {engine.current_state()}")
    elif args.command == "reset":
        engine.reset()
        print("KRXA EXEC ENGINE: RESET COMPLETE")
    elif args.command == "advance":
        print(f"STATE: {engine.advance('manual_advance')}")
    elif args.command == "run-m2m":
        run_demo(args.message)
    elif args.command == "input-flow":
        result = run_input_flow()
        print("KRXA INPUT FLOW CONNECT: PASS")
        print(f"INPUT: {result['input']}")
        print(f"INTENT: {result['intent']} ({result['intent_confidence']})")
        print(f"OUTPUT: {result['output']}")
        print(f"STATE: {result['state']}")
    elif args.command == "recover":
        engine.reconnect_and_recover()
        print(f"STATE: {engine.current_state()}")


if __name__ == "__main__":
    main()
