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
    parser.add_argument("--output-root", default=r"C:\\backups\\pg\\base")
    parser.add_argument("--s3-bucket", required=True)
    parser.add_argument("--kms-key-id", required=True)
    parser.add_argument("--pg-basebackup-path", default="pg_basebackup")
    parser.add_argument("--label-prefix", default="weekly")
    args = parser.parse_args()
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    local_dir = os.path.join(args.output_root, ts)
    pathlib.Path(local_dir).mkdir(parents=True, exist_ok=True)
    label = f"{args.label_prefix}-{ts}"
    env = os.environ.copy()
    env["PGPASSWORD"] = args.pg_password
    subprocess.run([args.pg_basebackup_path, "-h", args.pg_host, "-p", str(args.pg_port), "-U", args.pg_user, "-D", local_dir, "-F", "t", "-z", "-X", "none", "-P", "--checkpoint=fast", "--label", label], check=True, env=env)
    dest = f"{args.s3_bucket}/base/{ts}"
    subprocess.run(["aws", "s3", "cp", local_dir, dest, "--recursive", "--sse", "aws:kms", "--sse-kms-key-id", args.kms_key_id], check=True)

if __name__ == "__main__":
    main()