"""Pattern design agent — orchestrates conversation and pattern operations."""

import json
import logging
from typing import Optional

from .base import Message, ContentPart
from .context import ConversationContext, PatternContext
from .prompts import build_system_prompt
from .tools import PATTERN_TOOLS
from seamly2d.models.pattern import Pattern
from seamly2d.operations import (
    ModifyDart, AddDart, AddPocketOpening, UpdateMeasurement, SetSeamAllowance
)

logger = logging.getLogger(__name__)


def _pattern_summary(pattern: Pattern) -> str:
    """Build a concise JSON summary of the pattern for the system prompt."""
    draws = []
    for draw in pattern.draws:
        point_names = [getattr(pt, "name", f"id:{pt.id}") for pt in draw.points]
        draws.append({"name": draw.name, "points": point_names,
                      "lines": len(draw.lines), "splines": len(draw.splines),
                      "arcs": len(draw.arcs)})
    pieces = [{"name": p.name, "nodes": len(p.nodes)} for p in pattern.pieces]
    measurements = {}
    if pattern.measurements:
        measurements = {k: v.value for k, v in
                        list(pattern.measurements.measurements.items())[:15]}
    return json.dumps({
        "draws": draws,
        "pieces": pieces,
        "measurements": measurements,
        "unit": pattern.metadata.unit.value,
    }, indent=2)


class PatternDesignAgent:
    """Agentic loop: NL input → tool calls → pattern ops → updated pattern."""

    MAX_TOOL_ITERATIONS = 5

    def __init__(self, provider):
        self.provider = provider

    async def process_turn(
        self,
        user_text: str,
        attachments: list,  # list[ContentPart]
        conv_ctx: ConversationContext,
        pat_ctx: PatternContext,
    ) -> tuple:
        """Process one conversation turn.
        Returns (reply_text, updated_pattern, changed_ids).
        """
        # Build user message
        parts = [ContentPart.text(user_text)] + list(attachments)
        user_msg = Message(role="user", content=parts)
        conv_ctx.add(user_msg)

        system_prompt = build_system_prompt(
            _pattern_summary(pat_ctx.pattern),
            unit=pat_ctx.pattern.metadata.unit.value,
        )

        messages = conv_ctx.get_recent()
        changed_ids = []
        current_pattern = pat_ctx.pattern

        for iteration in range(self.MAX_TOOL_ITERATIONS):
            response = await self.provider.complete(
                messages=messages,
                system_prompt=system_prompt,
                tools=PATTERN_TOOLS,
                max_tokens=2048,
                temperature=0.2,
            )

            if not response.tool_calls:
                # Final text response — no more tools
                assistant_msg = Message.from_text("assistant", response.text)
                conv_ctx.add(assistant_msg)
                pat_ctx.pattern = current_pattern
                return response.text, current_pattern, changed_ids

            # Process tool calls
            tool_results = []
            assistant_content = []

            # Add text part if any
            if response.text:
                assistant_content.append({"type": "text", "text": response.text})

            for tool_call in response.tool_calls:
                tool_name, tool_input, tool_id = self._extract_tool_info(tool_call)
                assistant_content.append({
                    "type": "tool_use",
                    "id": tool_id,
                    "name": tool_name,
                    "input": tool_input,
                })

                result = self._execute_tool(tool_name, tool_input,
                                            current_pattern, pat_ctx)
                if result.get("success") and "pattern" in result:
                    pat_ctx.push_undo()
                    current_pattern = result.pop("pattern")
                    changed_ids.extend(result.get("changed_ids", []))

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps({k: v for k, v in result.items()
                                           if k not in ("pattern",)}),
                })

            # Add assistant message with tool uses
            messages.append({"role": "assistant", "content": assistant_content})
            # Add tool results as user message
            messages.append({"role": "user", "content": tool_results})

        # Fallback: get final response after max iterations
        final = await self.provider.complete(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=1024,
        )
        conv_ctx.add(Message.from_text("assistant", final.text))
        pat_ctx.pattern = current_pattern
        return final.text, current_pattern, changed_ids

    def _extract_tool_info(self, tool_call) -> tuple:
        """Extract (name, input_dict, id) from provider-specific tool call object."""
        # Anthropic tool_use block
        if hasattr(tool_call, "name"):
            return tool_call.name, dict(tool_call.input), tool_call.id
        # OpenAI tool call object
        if hasattr(tool_call, "function"):
            try:
                inp = json.loads(tool_call.function.arguments)
            except Exception:
                inp = {}
            return tool_call.function.name, inp, tool_call.id
        return str(tool_call), {}, "unknown"

    def _execute_tool(self, name: str, inp: dict,
                      pattern: Pattern, pat_ctx: PatternContext) -> dict:
        """Execute a tool and return a result dict."""
        try:
            if name == "get_pattern_summary":
                return {"success": True, "summary": _pattern_summary(pattern)}

            elif name == "update_measurement":
                op = UpdateMeasurement(inp["name"], float(inp["value"]))
                result = op.apply(pattern)
                return {"success": True, "pattern": result.pattern,
                        "message": result.message, "changed_ids": result.changed_ids}

            elif name == "modify_dart":
                op = ModifyDart(inp["draw_name"], inp["dart_base_point"],
                                inp["new_intake"])
                result = op.apply(pattern)
                return {"success": True, "pattern": result.pattern,
                        "message": result.message, "changed_ids": result.changed_ids}

            elif name == "add_dart":
                op = AddDart(
                    draw_name=inp["draw_name"],
                    seam_start_name=inp["seam_start"],
                    seam_end_name=inp["seam_end"],
                    intake_formula=inp.get("intake_formula", "(bust-waist)/6"),
                    length_formula=inp.get("length_formula", "12"),
                )
                result = op.apply(pattern)
                return {"success": True, "pattern": result.pattern,
                        "message": result.message, "changed_ids": result.changed_ids}

            elif name == "add_pocket_opening":
                op = AddPocketOpening(
                    draw_name=inp["draw_name"],
                    seam_start_name=inp["seam_start"],
                    seam_end_name=inp["seam_end"],
                    opening_width=str(inp.get("opening_width", "15")),
                    distance_from_start=str(inp.get("distance_from_start", "5")),
                )
                result = op.apply(pattern)
                return {"success": True, "pattern": result.pattern,
                        "message": result.message, "changed_ids": result.changed_ids}

            elif name == "set_seam_allowance":
                op = SetSeamAllowance(inp["piece_name"], float(inp["width"]))
                result = op.apply(pattern)
                return {"success": True, "pattern": result.pattern,
                        "message": result.message, "changed_ids": result.changed_ids}

            else:
                return {"success": False, "error": f"Unknown tool: {name}"}

        except Exception as e:
            logger.exception(f"Tool {name} failed: {e}")
            return {"success": False, "error": str(e)}
