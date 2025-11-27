import argparse
import os
import subprocess
import datetime
import pathlib

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, default=5432)
    parser.add_argument("--pg-user", required=True)
    parser.add_argument("--pg-password", required=True)
    parser.add_argument("--pg-database", required=True)
    parser.add_argument("--output-dir", default=r"C:\\backups\\pg\\dumps")
    parser.add_argument("--s3-bucket", required=True)
    parser.add_argument("--kms-key-id", required=True)
    parser.add_argument("--pg-dump-path", default="pg_dump")
    parser.add_argument("--compression-level", type=int, default=9)
    args = parser.parse_args()
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    pathlib.Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"{args.pg_database}-{ts}.dump"
    dump_path = os.path.join(args.output_dir, filename)
    env = os.environ.copy()
    env["PGPASSWORD"] = args.pg_password
    subprocess.run([args.pg_dump_path, "-h", args.pg_host, "-p", str(args.pg_port), "-U", args.pg_user, "-d", args.pg_database, "-F", "c", "-Z", str(args.compression_level), "-f", dump_path], check=True, env=env)
    dest = f"{args.s3_bucket}/dumps/{args.pg_database}/{filename}"
    subprocess.run(["aws", "s3", "cp", dump_path, dest, "--sse", "aws:kms", "--sse-kms-key-id", args.kms_key_id], check=True)

if __name__ == "__main__":
    main()