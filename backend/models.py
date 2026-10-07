"""Pydantic / PydanticAI structured types for the Campus Customs backend:
the API's request/response shapes (main.py's routes) and the agent's own
structured output type (what agent.py's Agent is constrained to return)."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class ProductSize(BaseModel):
    size: str
    quantity: int


class Product(BaseModel):
    """A full product card: everything the frontend needs to render a
    product (in the catalogue grid, a detail page, or a chat reply)."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image: str
    price: float
    sizes: list[ProductSize]


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


class AuthResponse(User):
    """What signup/login return: the user plus an opaque bearer session
    token. The frontend stores this token and sends it as
    `Authorization: Bearer <token>` on every authenticated request from then
    on — main.py resolves the real user_id from this token server-side, it
    never trusts a user_id the client merely claims (see sessions.py)."""

    session_token: str


class PageContext(BaseModel):
    """Where the shopper is in the storefront right now, sent by the frontend
    with every chat message. Lets the agent resolve a vague reference like
    "do you have this in pink" to the product the shopper is actually
    looking at, without the shopper having to name it again.

    Only `product_id` is trusted from the client. main.py looks up the real
    product name server-side from that id rather than trusting a client-
    supplied name — a shopper's browser could otherwise claim to be viewing
    a product with a fabricated name, which the agent might then repeat back
    as if it came from the catalogue."""

    page: Literal["home", "products", "product_detail", "about", "login", "create_account", "unknown"]
    product_id: str | None = Field(None, max_length=128, description="Set only when page is product_detail")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    page_context: PageContext | None = None

    @field_validator("message")
    @classmethod
    def strip_and_require_non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message cannot be blank")
        return stripped


class ChatResponse(BaseModel):
    """What main.py's /api/chat route returns to the frontend: a message
    plus full product cards for anything the agent referenced."""

    message: str
    products: list[Product] = []


class ChatHistoryMessage(BaseModel):
    """One past turn, reconstructed from the chat_messages table, for
    repopulating the chat widget when a logged-in shopper returns."""

    role: str
    content: str
    products: list[Product] = []


class ChatHistoryResponse(BaseModel):
    messages: list[ChatHistoryMessage] = []


class ProductRef(BaseModel):
    """Minimal pointer to a catalogue product, used only as part of the
    agent's structured output (see ChatReply) — main.py looks each one up
    and expands it into a full Product card before responding to the
    frontend."""

    product_id: str = Field(
        ..., description="Catalogue product ID, exactly as returned by search_products or get_product_stock"
    )
    name: str = Field(..., description="Product name")


class ChatReply(BaseModel):
    """Structured output type the PydanticAI agent (agent.py) is constrained
    to return for each turn."""

    message: str = Field(..., description="The assistant's reply to show the shopper")
    products: list[ProductRef] = Field(
        default_factory=list,
        description="Products mentioned or recommended in this reply, if any. Empty if none.",
    )


class ProductSearchResult(BaseModel):
    """One row returned by search_products_tool — just enough for the agent
    to decide which product(s) are relevant and then call a stock tool for
    exact numbers. Deliberately excludes stock/sizes (that's a separate,
    more expensive lookup the agent should only do once it knows which
    product it's answering about)."""

    product_id: str
    name: str
    garment_type: str
    description: str
    price: float


class SizeStock(BaseModel):
    size: str
    quantity: int
    in_stock: bool


class ProductStock(BaseModel):
    """Full per-size stock breakdown for one product, returned by
    get_product_stock_tool (single product) and get_stock_for_products_tool
    (as a list, for a deliberate bulk/plural request)."""

    product_id: str
    name: str
    price: float
    sizes: list[SizeStock]


class SizeAvailability(BaseModel):
    """Single-size stock check returned by check_size_availability_tool."""

    product_id: str
    name: str
    size: str
    quantity: int
    in_stock: bool


class ShopperContext(BaseModel):
    """Who's chatting and what they're looking at right now, returned by
    get_shopper_context_tool. Built entirely from ChatDeps (request-scoped
    state set by main.py before the turn starts) — this tool never touches
    the database itself, it just exposes state the agent can't otherwise see
    since it isn't part of the conversation text."""

    logged_in: bool
    first_name: str | None = Field(None, description="Only present when logged_in is True")
    page: str = Field(..., description="Same values as PageContext.page")
    viewing_product_id: str | None = None
    viewing_product_name: str | None = None
