# coding=utf-8
import asyncio
from aiohttp import ClientSession


class OutlineAPI(object):
    def __init__(self, api_url: str):
        self.api_url = api_url if api_url.endswith("/") else api_url + "/"
        self.session = ClientSession(self.api_url)

    async def close(self):
        await self.session.close()

    async def get_server_info(self) -> dict[str, str | int]:
        async with self.session.get("server", ssl=False) as response:
            return await response.json()

    async def get_access_keys(self) -> list[dict[str, str | int]]:
        async with self.session.get("access-keys", ssl=False) as response:
            return (await response.json()).get("accessKeys", [])

    async def create_access_key(
        self, name: str = None, password: str = None
    ) -> dict[str, str | int]:
        params = {}
        if name is not None:
            params["name"] = name
        if password is not None:
            params["password"] = password
        async with self.session.post(
            "access-keys",
            headers={"Content-Type": "application/json"},
            json=params,
            ssl=False,
        ) as response:
            if response.ok:
                return await response.json()
            else:
                raise Exception("Failed to create access key: " + await response.text())

    async def delete_access_key(self, key_id: int):
        async with self.session.delete(f"access-keys/{key_id}", ssl=False) as response:
            if not response.ok:
                raise KeyError(f"Access key {key_id} not found.")

    async def get_bandwidth_usage(self) -> dict[str, int]:
        async with self.session.get("metrics/transfer", ssl=False) as response:
            return (await response.json()).get("bytesTransferredByUserId", {})


async def main():
    from pprint import pprint
    from dotenv import load_dotenv
    from os import getenv

    load_dotenv("TOKEN.env")
    api_url = getenv("OUTLINE_API_URL")
    client = OutlineAPI(api_url)
    pprint(await client.get_server_info())
    await client.close()
    # await client.delete_access_key(8)


if __name__ == "__main__":
    asyncio.run(main())
