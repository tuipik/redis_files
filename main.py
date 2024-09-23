import os
import sys
import time

import redis
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def _get_files(folder, redis_client):
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            redis_client.sadd('file_paths', file_path)
            logging.info(f"Fadded {file_path} {time.time()}\n")
            sys.stdout.write(f"added {file_path} {time.time()}\n")
            yield file_path


async def _check_files(folder, redis_client):
    logging.info(f"AAAAAAAAAAAAAAAAAAAAAAA.")
    while True:
        file_paths_in_redis = redis_client.smembers('file_paths')
        logging.info(f"Found {len(file_paths_in_redis)} file paths in Redis.")
        for file_path in file_paths_in_redis:
            if not os.path.exists(file_path):
                redis_client.srem('file_paths', file_path)
                sys.stdout.write(f"deleted {file_path}\n")
        await asyncio.sleep(18)


async def check_files(folder, redis_host, redis_port):
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    await _check_files(folder, redis_client)


async def get_files(folder, redis_host, redis_port):
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    _get_files(folder, redis_client)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add file paths to Redis and check periodically.")
    parser.add_argument("folder", help="Path to the folder")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6388, help="Redis port")

    args = parser.parse_args()

    asyncio.run(check_files(args.folder, args.redis_host, args.redis_port))
