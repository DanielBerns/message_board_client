import asyncio
import argparse
from message_board_client.core import MessageBoardClient
from typing import List, Dict, Any

async def background_heartbeat(client: MessageBoardClient, interval: int = 30) -> None:
    """A typed background task that sends a heartbeat every X seconds."""
    try:
        while True:
            await client.send_heartbeat()
            print("[System] Heartbeat sent.")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        print("[System] Heartbeat task cancelled.")

async def main(config_path: str) -> None:
    """Main execution block taking the config path dynamically."""
    # Initialize the secure client using the provided config file
    async with MessageBoardClient(config_path) as client:

        heartbeat_task: asyncio.Task[None] = asyncio.create_task(
            background_heartbeat(client, interval=10)
        )

        print(f"\n--- Logged in as {client.username} ---")

        print("\n--- Subscribing to Tags ---")
        await client.subscribe_tags(tags=["announcement", "tech"])

        print("\n--- Sending Secure Messages ---")
        await client.send_public_message(tags=["tech"], content="Strictly typed and encrypted broadcast!")

        # Using the group message endpoint
        await client.send_group_message(recipients=["nimda", "test_client"], content="Secure group sync.")

        print("\n--- Fetching Decrypted Public Messages ---")
        messages: List[Dict[str, Any]] = await client.get_public_messages()
        for msg in messages:
            print(f"[{msg.get('sender', 'Unknown')}] {msg.get('content')}")

        await asyncio.sleep(15)
        heartbeat_task.cancel()
        await client.logout()

if __name__ == "__main__":
    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(description="Secure Message Board Client run script.")
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.yaml",
        help="Path to the YAML configuration file (default: config.yaml)"
    )

    # Parse the arguments provided in the CLI
    args = parser.parse_args()

    try:
        # Pass the parsed config path to the main async function
        asyncio.run(main(args.config))
    except KeyboardInterrupt:
        print("\n[System] Client stopped by user.")
    except FileNotFoundError:
        print(f"\n[Error] Configuration file '{args.config}' not found. Please provide a valid path.")
