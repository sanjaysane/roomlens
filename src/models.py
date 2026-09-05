"""Domain constants: roles, conversational states, statuses.

The state machine is declarative: ROUTES in state_machine.py maps
(role, state) -> handler. These names are the contract between the
dispatcher, the handlers, and the tests.
"""

from __future__ import annotations

# ── Roles ──────────────────────────────────────────────────────────
ROLE_DESIGNER = "designer"
ROLE_PROSPECT = "prospect"

# ── Prospect states ────────────────────────────────────────────────
P_NEW = "prospect_new"  # welcome + "1 = designer, 2 = preview furniture"
P_PICK_DESIGNER = "prospect_pick_designer"  # choose a designer (single digit)
P_PHOTO = "prospect_photo"  # guided room-photo capture
P_RETAKE = "prospect_retake"  # (same handling as P_PHOTO; kept for clarity)
P_WAITING = "prospect_waiting"  # preview being prepared
P_REVIEW = "prospect_review"  # 1 = order, 2 = placement, 3 = product, 4 = talk
P_ORDER = "prospect_order_confirm"  # 1 = confirm 👍, 2 = cancel 👎
P_TRACKING = "prospect_tracking"  # order status updates
P_LANGUAGE = "language_select"  # 1 = en, 2 = es, 3 = hi (any state)

# ── Designer states ────────────────────────────────────────────────
D_NEW = "designer_new"  # one-time studio-name setup
D_HOME = "designer_home"  # hub: 1 catalog, 2 studio, 3 orders, 4 marketing
D_CATALOG = "designer_catalog"  # list; 1 = add, 0 = back
D_CAT_NAME = "designer_catalog_name"  # typed product name (setup exception)
D_CAT_PRICE = "designer_catalog_price"  # typed price
D_CAT_SIZE = "designer_catalog_size"  # 1 floor, 2 wall, 3 tabletop
D_CAT_PHOTO = "designer_catalog_photo"  # optional cutout upload, 0 = skip
D_CAT_REMOVE = "designer_catalog_remove"  # pick product to deactivate
D_STUDIO = "designer_studio"  # pending room photos
D_STUDIO_PRODUCT = "designer_studio_product"  # pick product to place
D_STUDIO_PRESET = "designer_studio_preset"  # pick placement preset
D_STUDIO_ADJUST = "designer_studio_adjust"  # bigger/smaller/send/restart
D_ORDERS = "designer_orders"  # inbound order queue
D_ORDER_STATUS = "designer_order_status"  # 1 preparing, 2 shipped, 3 delivered
D_MARKETING = "designer_marketing"  # 1 campaign, 2 follow-ups, 3 win-back, 4 list
D_CAMP_BODY = "designer_campaign_body"  # typed campaign text (setup exception)
D_CAMP_CONFIRM = "designer_campaign_confirm"  # 1 = send to opted-in

# ── Placement presets (compositing engine) ─────────────────────────
PRESET_FLOOR_CENTER = "floor-center"
PRESET_LEFT_WALL = "left-wall"
PRESET_RIGHT_WALL = "right-wall"
PRESET_WALL_HANG = "wall-hang"
PLACEMENT_PRESETS = (
    PRESET_FLOOR_CENTER,
    PRESET_LEFT_WALL,
    PRESET_RIGHT_WALL,
    PRESET_WALL_HANG,
)

# ── Size classes → default preset ──────────────────────────────────
SIZE_FLOOR = "floor"
SIZE_WALL = "wall"
SIZE_TABLETOP = "tabletop"
SIZE_CLASS_DEFAULT_PRESET = {
    SIZE_FLOOR: PRESET_FLOOR_CENTER,
    SIZE_WALL: PRESET_WALL_HANG,
    SIZE_TABLETOP: PRESET_LEFT_WALL,
}

# ── Order statuses (mirror the SQL enum) ───────────────────────────
OPEN_ORDER_STATUSES = ("received", "preparing", "out_for_delivery")

SUPPORTED_LANGUAGES = ("en", "es", "hi", "mr")
LANGUAGE_OPTIONS = (("1", "en"), ("2", "es"), ("3", "hi"), ("4", "mr"))

# Words (any supported language) that open the language menu mid-chat.
LANGUAGE_COMMANDS = {"language", "idioma", "भाषा", "lang", "lenguaje"}
