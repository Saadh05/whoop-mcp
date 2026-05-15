#!/usr/bin/env python3
import json
import asyncio
from datetime import datetime, timedelta, timezone
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from whoop_client import WhoopClient

server = Server("whoop-mcp")
whoop = WhoopClient()


def _fmt(obj: object) -> str:
    return json.dumps(obj, indent=2, default=str)


def _default_range(days: int = 30) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return start, end


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_profile",
            description="Get your Whoop user profile (name, email, etc.)",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_body_measurement",
            description="Get your body measurements (height, weight, max heart rate)",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_recovery",
            description=(
                "Get recovery scores including HRV, resting heart rate, sleep performance, "
                "and recovery percentage. Defaults to the last 30 days."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Start date in ISO 8601 format (e.g. 2025-01-01T00:00:00Z). Defaults to 30 days ago.",
                    },
                    "end": {
                        "type": "string",
                        "description": "End date in ISO 8601 format. Defaults to now.",
                    },
                },
            },
        ),
        types.Tool(
            name="get_sleep",
            description=(
                "Get sleep data including duration, efficiency, disturbances, "
                "and sleep stage breakdown. Defaults to the last 30 days."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Start date in ISO 8601 format. Defaults to 30 days ago.",
                    },
                    "end": {
                        "type": "string",
                        "description": "End date in ISO 8601 format. Defaults to now.",
                    },
                },
            },
        ),
        types.Tool(
            name="get_workouts",
            description=(
                "Get workout data including sport type, strain score, heart rate zones, "
                "calories, and duration. Defaults to the last 30 days."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Start date in ISO 8601 format. Defaults to 30 days ago.",
                    },
                    "end": {
                        "type": "string",
                        "description": "End date in ISO 8601 format. Defaults to now.",
                    },
                },
            },
        ),
        types.Tool(
            name="get_cycles",
            description=(
                "Get physiological cycles (day-level data) including daily strain, "
                "kilojoules burned, and average/max heart rate. Defaults to the last 30 days."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Start date in ISO 8601 format. Defaults to 30 days ago.",
                    },
                    "end": {
                        "type": "string",
                        "description": "End date in ISO 8601 format. Defaults to now.",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "get_profile":
            data = whoop.get_profile()
            return [types.TextContent(type="text", text=_fmt(data))]

        elif name == "get_body_measurement":
            data = whoop.get_body_measurement()
            return [types.TextContent(type="text", text=_fmt(data))]

        elif name == "get_recovery":
            start = arguments.get("start") or _default_range()[0]
            end = arguments.get("end") or _default_range()[1]
            data = whoop.get_recovery(start, end)
            summary = _summarize_recovery(data)
            return [types.TextContent(type="text", text=f"{summary}\n\nRaw data:\n{_fmt(data)}")]

        elif name == "get_sleep":
            start = arguments.get("start") or _default_range()[0]
            end = arguments.get("end") or _default_range()[1]
            data = whoop.get_sleep(start, end)
            summary = _summarize_sleep(data)
            return [types.TextContent(type="text", text=f"{summary}\n\nRaw data:\n{_fmt(data)}")]

        elif name == "get_workouts":
            start = arguments.get("start") or _default_range()[0]
            end = arguments.get("end") or _default_range()[1]
            data = whoop.get_workouts(start, end)
            summary = _summarize_workouts(data)
            return [types.TextContent(type="text", text=f"{summary}\n\nRaw data:\n{_fmt(data)}")]

        elif name == "get_cycles":
            start = arguments.get("start") or _default_range()[0]
            end = arguments.get("end") or _default_range()[1]
            data = whoop.get_cycles(start, end)
            summary = _summarize_cycles(data)
            return [types.TextContent(type="text", text=f"{summary}\n\nRaw data:\n{_fmt(data)}")]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


def _summarize_recovery(records: list) -> str:
    if not records:
        return "No recovery data found."
    scores = [r["score"]["recovery_score"] for r in records if r.get("score")]
    hrvs = [r["score"]["hrv_rmssd_milli"] for r in records if r.get("score")]
    rhrs = [r["score"]["resting_heart_rate"] for r in records if r.get("score")]
    lines = [f"Recovery summary ({len(records)} days):"]
    if scores:
        lines.append(f"  Avg recovery score: {sum(scores)/len(scores):.1f}%  (min {min(scores):.0f}%, max {max(scores):.0f}%)")
    if hrvs:
        lines.append(f"  Avg HRV (RMSSD): {sum(hrvs)/len(hrvs):.1f} ms")
    if rhrs:
        lines.append(f"  Avg resting HR: {sum(rhrs)/len(rhrs):.1f} bpm")
    return "\n".join(lines)


def _summarize_sleep(records: list) -> str:
    if not records:
        return "No sleep data found."
    lines = [f"Sleep summary ({len(records)} sessions):"]
    durations = []
    efficiencies = []
    for r in records:
        score = r.get("score") or {}
        stage = r.get("score", {}).get("stage_summary", {})
        total_ms = (
            stage.get("total_light_sleep_time_milli", 0)
            + stage.get("total_slow_wave_sleep_time_milli", 0)
            + stage.get("total_rem_sleep_time_milli", 0)
            + stage.get("total_awake_time_milli", 0)
        )
        if total_ms:
            durations.append(total_ms / 3_600_000)
        eff = score.get("sleep_efficiency_percentage")
        if eff:
            efficiencies.append(eff)
    if durations:
        lines.append(f"  Avg duration: {sum(durations)/len(durations):.1f} hrs  (min {min(durations):.1f}, max {max(durations):.1f})")
    if efficiencies:
        lines.append(f"  Avg sleep efficiency: {sum(efficiencies)/len(efficiencies):.1f}%")
    return "\n".join(lines)


def _summarize_workouts(records: list) -> str:
    if not records:
        return "No workout data found."
    strains = [r["score"]["strain"] for r in records if r.get("score")]
    cals = [r["score"]["kilojoule"] * 0.239 for r in records if r.get("score")]
    sports: dict[str, int] = {}
    for r in records:
        sport = r.get("sport_id", "unknown")
        sports[sport] = sports.get(sport, 0) + 1
    lines = [f"Workout summary ({len(records)} sessions):"]
    if strains:
        lines.append(f"  Avg strain: {sum(strains)/len(strains):.1f}  (max {max(strains):.1f})")
    if cals:
        lines.append(f"  Avg calories: {sum(cals)/len(cals):.0f} kcal")
    return "\n".join(lines)


def _summarize_cycles(records: list) -> str:
    if not records:
        return "No cycle data found."
    strains = [r["score"]["strain"] for r in records if r.get("score")]
    kjs = [r["score"]["kilojoule"] for r in records if r.get("score")]
    lines = [f"Cycle summary ({len(records)} days):"]
    if strains:
        lines.append(f"  Avg daily strain: {sum(strains)/len(strains):.1f}")
    if kjs:
        kcals = [kj * 0.239 for kj in kjs]
        lines.append(f"  Avg daily calories burned: {sum(kcals)/len(kcals):.0f} kcal")
    return "\n".join(lines)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
