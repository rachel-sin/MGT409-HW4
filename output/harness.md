# Database Field Reference — campus_customs.db

## catalogue

| Field | Why it matters |
|---|---|
| product_id | Unique key for each product; every other table references the product through this id |
| name | Human-readable product name shown to shoppers and used in search results |
| garment_type | Lets you filter/group products by type (t-shirt, hoodie, etc.) rather than parsing the name |
| description | Marketing copy a shopping assistant can surface or summarize when recommending the item |
| colors | Tells a buyer (or an agent) what color options exist before checking stock |
| search_tags | Keyword list that powers search/matching so queries don't have to rely on exact name matches |
| image_file_path | Points to the product photo so a UI or chatbot can display the item visually |
| price | Needed for any purchase decision, budget filtering, or order total calculation |

## inventory

| Field | Why it matters |
|---|---|
| id | Internal row identifier for each size-variant record |
| product_id | Links a stock record back to the specific product in catalogue |
| size | Distinguishes stock levels by size since a product isn't a single sellable unit |
| quantity | Tells you whether an item is actually available to sell/recommend right now |

## users

| Field | Why it matters |
|---|---|
| id | Unique key for each account, referenced by chat_messages to tie conversations to a person |
| name / first_name / last_name | Used for personalization (greetings, order confirmations) |
| email | Login identifier and contact point for the account |
| password_hash | Verifies login without ever storing a plaintext password |
| created_at | Tracks account age, useful for auditing or "new user" logic |
