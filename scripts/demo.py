import asyncio
from message_client import MessageBoardClient

async def background_heartbeat(client: MessageBoardClient, interval: int = 30):
    """A background task that sends a heartbeat every X seconds."""
    try:
        while True:
            await client.send_heartbeat()
            print("[System] Heartbeat sent.")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        print("[System] Heartbeat task cancelled.")

async def main():
    # Initialize the client using the config file
    async with MessageBoardClient('config.yaml') as client:

        # Start the background heartbeat task
        heartbeat_task = asyncio.create_task(background_heartbeat(client, interval=10))

        # Perform asynchronous API calls
        print("\n--- Sending Messages ---")
        await client.send_public_message(tags=["general", "tech"], content="Hello from the async python client!")
        await client.send_private_message(recipient="admin", content="Reporting for duty.")

        print("\n--- Fetching Public Messages ---")
        messages = await client.get_public_messages(tags=["general"])
        for msg in messages:
            print(f"[{msg.get('sender', 'Unknown')}] {msg.get('content')}")

        print("\n--- Fetching Heartbeats ---")
        heartbeats = await client.get_heartbeats()
        print(heartbeats)

        # Let the background task run for a bit to demonstrate concurrency
        await asyncio.sleep(15)

        # Clean up
        heartbeat_task.cancel()
        await client.logout()

if __name__ == "__main__":
    asyncio.run(main())
