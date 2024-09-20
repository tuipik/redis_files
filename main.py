import os
import sys

import redis
import asyncio


async def get_files(folder, redis_client):
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            redis_client.sadd('file_paths', file_path)
            sys.stdout.write(f"added {file_path}")
            yield file_path


async def check_files(folder, redis_client):
    while True:
        async for file_path in get_files(folder, redis_client):
            if not redis_client.sismember('file_paths', file_path):
                redis_client.sadd('file_paths', file_path)
        await asyncio.sleep(1800)  # 30 minutes


async def main(folder, redis_host, redis_port):
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    await check_files(folder, redis_client)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add file paths to Redis and check periodically.")
    parser.add_argument("folder", help="Path to the folder")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6388, help="Redis port")

    args = parser.parse_args()

    asyncio.run(main(args.folder, args.redis_host, args.redis_port))
