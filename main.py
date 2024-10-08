from datetime import datetime
import os
import logging
import redis

logging.basicConfig(level=logging.INFO)


def scan_and_store_paths(base_path):
    pipe = r.pipeline()
    count = 0
    batch_size = 10000

    for root, dirs, files in os.walk(base_path):
        for file in files:
            file_path = os.path.join(root, file)
            pipe.set(file_path, "")
            count += 1

            if count % batch_size == 0:
                pipe.execute()
                logging.info(f"Processed {count} files")

    pipe.execute()
    logging.info(f"Total inserted: {count} files")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Add file paths to Redis."
    )
    parser.add_argument("folder", help="Path to the folder")
    parser.add_argument("--redis_host", default="localhost", help="Redis host")
    parser.add_argument("--redis_port", type=int, default=6388, help="Redis port")

    args = parser.parse_args()

    init_file = os.path.join(args.folder, "init_file.txt")
    if not os.path.exists(init_file):
        logging.info("Start ...")
        start_time = datetime.now()

        r = redis.Redis(host=args.redis_host, port=args.redis_port, db=0)
        print(r.ping())
        scan_and_store_paths(args.folder)

        logging.info(f"Completed in: {datetime.now() - start_time}")
        with open(init_file, "w") as f:
            f.write("Delete me if you want to add all file paths from dir to redis.")
    else:
        logging.info(f"File paths already added. Delete '{init_file}' if you want to add all file paths from dir to redis.")
