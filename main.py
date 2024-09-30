from datetime import datetime
import os
import logging
import redis.asyncio as aioredis
import asyncio
import concurrent.futures

logging.basicConfig(level=logging.INFO)


async def push_paths_to_redis(folder, redis_client):
    chunk_size = 1000
    chunks = set()
    counter = 0
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)
            chunks.add(file_path)
            if len(chunks) == chunk_size:
                await redis_client.sadd("file_paths", *chunks)
                chunks.clear()
                counter += chunk_size
    if chunks:
        await redis_client.sadd("file_paths", *chunks)
        counter += len(chunks)
        chunks.clear()
    logging.info(f"Added {counter} paths to redis")


def get_all_directories(folder):
    directories = set()
    for root, dirs, files in os.walk(folder):
        if files:
            directories.add(root)
    return directories


async def process_directory(folder, redis_host, redis_port):
    redis_client = aioredis.Redis(
        host=redis_host, port=redis_port, decode_responses=True
    )
    try:
        await push_paths_to_redis(folder, redis_client)
    except Exception as e:
        logging.error(f"Error processing directory {folder}: {e}")
    finally:
        await redis_client.close()


def process_directory_sync(directory, redis_host, redis_port):
    asyncio.run(process_directory(directory, redis_host, redis_port))


async def main(directories, redis_host, redis_port):
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=20
    ) as executor:
        futures = [
            executor.submit(process_directory_sync, directory, redis_host, redis_port)
            for directory in directories
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error in process: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Add file paths to Redis using multiple processes."
    )
    parser.add_argument("folder", help="Path to the folder")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6388, help="Redis port")

    args = parser.parse_args()
    init_file = os.path.join(args.folder, "init_file.txt")
    if not os.path.exists(init_file):
        start_time = datetime.now()
        all_directories = get_all_directories(args.folder)

        asyncio.run(main(all_directories, args.redis_host, args.redis_port))

        logging.info(f"Remain time: {datetime.now() - start_time}")
        with open(init_file, "w") as f:
            f.write("Delete me if you want to add all file paths from dir to redis.")
    else:
        logging.info(f"File paths already added. Delete '{init_file}' if you want to add all file paths from dir to redis.")
