import aiohttp
import os

TOKEN = os.getenv("TOKEN")

async def respond_cv2(interaction, components: list, ephemeral: bool = False):
    flags = 1 << 15
    if ephemeral:
        flags |= 1 << 6
    payload = {"type": 4, "data": {"flags": flags, "components": components}}
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"https://discord.com/api/v10/interactions/{interaction.id}/{interaction.token}/callback",
            json=payload
        ) as r:
            if r.status not in (200, 204):
                print(f"[CV2:respond] {r.status} {await r.text()}")

async def update_cv2(interaction, components: list):
    payload = {"type": 7, "data": {"flags": 1 << 15, "components": components}}
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"https://discord.com/api/v10/interactions/{interaction.id}/{interaction.token}/callback",
            json=payload
        ) as r:
            if r.status not in (200, 204):
                print(f"[CV2:update] {r.status} {await r.text()}")

async def followup_cv2(interaction, components: list, ephemeral: bool = False):
    flags = 1 << 15
    if ephemeral:
        flags |= 1 << 6
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"https://discord.com/api/v10/webhooks/{interaction.application_id}/{interaction.token}",
            json={"flags": flags, "components": components}
        ) as r:
            if r.status not in (200, 204):
                print(f"[CV2:followup] {r.status} {await r.text()}")

async def send_cv2(channel_id: int, components: list) -> dict | None:
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as s:
        async with s.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            json={"flags": 1 << 15, "components": components},
            headers=headers
        ) as r:
            if r.status not in (200, 204):
                print(f"[CV2:send] {r.status} {await r.text()}")
                return None
            try:
                return await r.json()
            except Exception:
                return None

async def edit_cv2(channel_id: int, message_id: int, components: list):
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as s:
        async with s.patch(
            f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}",
            json={"flags": 1 << 15, "components": components},
            headers=headers
        ) as r:
            if r.status not in (200, 204):
                print(f"[CV2:edit] {r.status} {await r.text()}")

async def no_access(interaction, msg: str = "Δεν έχεις δικαίωμα για αυτή την εντολή."):
    await respond_cv2(interaction, [
        {"type": 17, "accent_color": 0xED4245, "components": [
            {"type": 10, "content": f"> Access Denied\n{msg}"}
        ]}
    ], ephemeral=True)
