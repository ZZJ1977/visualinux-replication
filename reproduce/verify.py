"""Recalculate the published counts and timings using the Python standard library."""

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify_queries(path):
    cases = json.loads(path.read_text(encoding="utf-8"))
    check(set(cases) == {"01", "02", "03", "06", "10", "11", "15", "16", "17", "21"},
          "Unexpected set of ViewQL cases")
    mismatches = []
    for case, report in cases.items():
        checks = report["original"]
        check(checks and report["query"].strip(), f"Missing query or checks in case {case}")
        effects_match = []
        for effect in checks:
            matches = (effect["expected"] == effect["changed"]
                       and not effect["missing"] and not effect["extra"])
            expected_status = "verified" if matches else "mismatch"
            check(effect["status"] == expected_status, f"Inconsistent recorded status in {case}")
            effects_match.append(matches)
        if not all(effects_match):
            mismatches.append(case)
    check(set(mismatches) == {"01", "15", "17"}, "Unexpected ViewQL mismatches")
    irq = cases["03"]["original"][0]
    check((irq["candidates"], irq["changed"]) == (16, 8), "Unexpected IRQ results")
    print("ViewQL: 7/10 original cases match the archived graph criteria; IRQ 8/16.")


def verify_timings(path):
    timings = defaultdict(dict)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            case, trial = int(row["table4"]), int(row["trial"])
            elapsed = float(row["total_ms"])
            check(trial not in timings[case], f"Duplicate case/trial {case}/{trial}")
            check(math.isfinite(elapsed) and elapsed > 0, "Invalid duration")
            check(int(row["objects"]) > 0 and int(row["bytes"]) > 0, "Missing extracted data")
            timings[case][trial] = elapsed
    check(set(timings) == set(range(1, 21)), "Expected the 20 table 4 rows")
    check(all(set(group) == {1, 2, 3} for group in timings.values()), "Missing trials")
    samples = [t for group in timings.values() for t in group.values()]
    print(f"QEMU: {len(samples)} samples, {min(samples):.1f} to {max(samples):.1f} ms.")
    print(f"Process tree: {statistics.mean(timings[1].values()):.1f} ms mean over 3 trials.")


def verify_capture(directory):
    index = json.loads((directory / "demo-index.json").read_text(encoding="utf-8"))
    stages = index["stages"]
    check([s["stage"] for s in stages] == [1, 2, 3], "Incorrect checkpoint sequence")
    for field in ("parent_pid", "socket_addr", "mapping_addr", "vm_start", "vm_end"):
        check(len({s[field] for s in stages}) == 1, f"{field} changed across checkpoints")
    for s in stages:
        middle = s["stage"] == 2
        lengths = [5, 11] if middle else []
        names = ["demo-anchor", "demo-new"] if middle else ["demo-anchor"]
        check(sorted(p["comm"] for p in s["children"]) == names, "Unexpected child names")
        check(s["qlen"] == len(lengths) and s["packet_lengths"] == lengths, "Unexpected queue")
        check(int(s["vm_end"], 16) - int(s["vm_start"], 16) == 4096, "Unexpected page size")
        check(bool(int(s["vm_flags"], 16) & 2) == (s["stage"] == 1), "Unexpected VM_WRITE")
        for kind in ("process", "queue", "mapping"):
            path = directory / f"stage-{s['stage']}-{kind}.json"
            graph = json.loads(path.read_text(encoding="utf-8"))[f"demo_{kind}"]
            boxes = graph["pool"]["boxes"]
            roots = graph["plot"]
            check(len(roots) == 1 and roots[0] in boxes, f"Missing root in {path.name}")

            def members(key):
                return boxes[key]["absts"]["default"]["members"]

            if kind == "queue":
                check(roots[0] == s["socket_addr"] + ":sock", "Unexpected receiver")
                check(int(members(roots[0])["qlen"]["value"]) == len(lengths), "Wrong queue length")
                observed = sorted(int(members(k)["len"]["value"]) for k in boxes
                                  if boxes[k]["type"] == "sk_buff")
                check(observed == lengths, "Unexpected packet lengths in graph")
            elif kind == "mapping":
                region = members(s["mapping_addr"] + ":vm_area_struct")
                check(all(region[k]["value"] == s[k] for k in ("vm_start", "vm_end", "vm_flags")),
                      "Mapping differs between graph and GDB")
            else:
                check(int(members(roots[0])["pid"]["value"]) == s["parent_pid"], "Wrong parent")
                children = {(int(members(k)["pid"]["value"]), int(members(k)["ppid"]["value"]),
                             members(k)["comm"]["value"]) for k in boxes
                            if boxes[k]["type"] == "task_struct" and k != roots[0]}
                check(children == {(p["pid"], p["ppid"], p["comm"]) for p in s["children"]},
                      "Children differ between graph and GDB")
    print(f"Capture {directory.name}: 3 checkpoints and 9 graphs verified.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, help="verify only this new 3-stage capture")
    args = parser.parse_args()
    if args.capture:
        verify_capture(args.capture)
        return
    root = Path(__file__).resolve().parents[1]
    verify_queries(root / "results" / "table3.json")
    verify_timings(root / "results" / "table4.csv")
    custom = sorted((root / "results" / "custom").glob("*/demo-index.json"))
    check(len(custom) == 2, "Expected two archived captures")
    for index in custom:
        verify_capture(index.parent)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError) as error:
        sys.exit(f"Verification failed: {error}")
