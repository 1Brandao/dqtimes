import argparse
import os
import subprocess
import datetime
import pathlib
import tempfile

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pg-host", required=True)
    parser.add_argument("--pg-port", type=int, default=5432)
    parser.add_argument("--pg-user", required=True)
    parser.add_argument("--pg-password", required=True)
    parser.add_argument("--target-database", required=True)
    parser.add_argument("--source-s3-url", required=True)
    parser.add_argument("--pg-restore-path", default="pg_restore")
    parser.add_argument("--createdb-path", default="createdb")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    temp_dir = tempfile.mkdtemp(prefix="pg-restore-")
    local_file = os.path.join(temp_dir, f"restore-{ts}.dump")
    subprocess.run(["aws", "s3", "cp", args.source_s3_url, local_file], check=True)
    env = os.environ.copy()
    env["PGPASSWORD"] = args.pg_password
    subprocess.run([args.createdb_path, "-h", args.pg_host, "-p", str(args.pg_port), "-U", args.pg_user, args.target_database], check=True, env=env)
    subprocess.run([args.pg_restore_path, "-h", args.pg_host, "-p", str(args.pg_port), "-U", args.pg_user, "-d", args.target_database, "-j", str(args.jobs), local_file], check=True, env=env)

if __name__ == "__main__":
    main()