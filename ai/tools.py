"""Tool definitions for the pattern design agent.

These are provided to the LLM so it can call structured operations.
Format follows Anthropic's tool schema (also converted for OpenAI in provider).
"""

PATTERN_TOOLS = [
    {
        "name": "modify_dart",
        "description": (
            "Modify an existing dart's intake depth. "
            "The dart is identified by its base/pivot point name. "
            "The new_intake is a formula string like '(bust-waist)/8'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "draw_name": {
                    "type": "string",
                    "description": "Name of the draw block, e.g. 'Bodice Front'",
                },
                "dart_base_point": {
                    "type": "string",
                    "description": "Name of the dart pivot/base point, e.g. 'D1'",
                },
                "new_intake": {
                    "type": "string",
                    "description": "New intake formula, e.g. '(bust-waist)/8' or '3.5'",
                },
            },
            "required": ["draw_name", "dart_base_point", "new_intake"],
        },
    },
    {
        "name": "add_dart",
        "description": (
            "Add a new dart to a draw block. "
            "Inserts dart intake points along a seam segment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "draw_name": {"type": "string"},
                "seam_start": {
                    "type": "string",
                    "description": "Name of seam start point",
                },
                "seam_end": {
                    "type": "string",
                    "description": "Name of seam end point",
                },
                "intake_formula": {
                    "type": "string",
                    "description": "Dart intake width formula, e.g. '(bust-waist)/6'",
                },
                "length_formula": {
                    "type": "string",
                    "description": "Dart length (depth) formula, e.g. '12'",
                },
            },
            "required": ["draw_name", "seam_start", "seam_end"],
        },
    },
    {
        "name": "add_pocket_opening",
        "description": (
            "Add a pocket opening on a seam line between two named points. "
            "Inserts PktTop and PktBot points along the seam."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "draw_name": {"type": "string"},
                "seam_start": {
                    "type": "string",
                    "description": "Name of seam start point",
                },
                "seam_end": {
                    "type": "string",
                    "description": "Name of seam end point",
                },
                "opening_width": {
                    "type": "string",
                    "description": "Pocket opening width in cm, e.g. '15'",
                },
                "distance_from_start": {
                    "type": "string",
                    "description": "Distance from seam_start to top of pocket, e.g. '5'",
                },
            },
            "required": ["draw_name", "seam_start", "seam_end", "opening_width"],
        },
    },
    {
        "name": "update_measurement",
        "description": "Update the value of a body measurement variable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Measurement name, e.g. 'bust', 'waist', 'hip', 'height'",
                },
                "value": {
                    "type": "number",
                    "description": "New value in the pattern's unit (cm or inch)",
                },
            },
            "required": ["name", "value"],
        },
    },
    {
        "name": "set_seam_allowance",
        "description": "Enable and set the seam allowance width on a pattern piece.",
        "input_schema": {
            "type": "object",
            "properties": {
                "piece_name": {"type": "string"},
                "width": {
                    "type": "number",
                    "description": "Seam allowance width in pattern units (cm)",
                },
            },
            "required": ["piece_name", "width"],
        },
    },
    {
        "name": "get_pattern_summary",
        "description": (
            "Get a JSON summary of the current pattern structure: "
            "draw blocks, point names, pieces, and measurements. "
            "Use this to understand the pattern before making changes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
