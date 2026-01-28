from pathlib import Path
import subprocess
import sys

def main():
    root = Path(__file__).resolve().parents[1]
    demo_in = root / "demo" / "demo_inputs"
    out = root / "demo" / "demo_outputs"
    out.mkdir(parents=True, exist_ok=True)

    # Run via module entrypoint
    cmd = [sys.executable, "-m", "mrb_longterm.cli", "--input", str(demo_in), "--output", str(out)]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
    print("Outputs written to:", out)

if __name__ == "__main__":
    main()
