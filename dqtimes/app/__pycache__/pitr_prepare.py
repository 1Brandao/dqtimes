import argparse
import os
import subprocess
import pathlib
import tempfile
import datetime
import tarfile

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-backup-s3-prefix", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--restore-command", required=True)
    parser.add_argument("--recovery-target-time")
    parser.add_argument("--pg-service-name")
    args = parser.parse_args()
    pathlib.Path(args.data_dir).mkdir(parents=True, exist_ok=True)
    work_dir = tempfile.mkdtemp(prefix="pitr-")
    subprocess.run(["aws", "s3", "sync", args.base_backup_s3_prefix, work_dir], check=True)
    for p in pathlib.Path(work_dir).glob("*.tar*"):
        mode = "r:gz" if str(p).endswith((".tar.gz", ".tgz")) else "r"
        with tarfile.open(p, mode) as tf:
            tf.extractall(args.data_dir)
    pathlib.Path(os.path.join(args.data_dir, "recovery.signal")).write_text("")
    auto_conf_path = os.path.join(args.data_dir, "postgresql.auto.conf")
    lines = []
    lines.append(f"restore_command = '{args.restore_command}'")
    if args.recovery_target_time:
        lines.append(f"recovery_target_time = '{args.recovery_target_time}'")
    lines.append("recovery_target_action = 'promote'")
    with open(auto_conf_path, "w", encoding="ascii") as f:
        f.write("\n".join(lines))
    if args.pg_service_name:
        subprocess.run(["powershell", "-Command", f"Start-Service -Name {args.pg_service_name}"]) 

if __name__ == "__main__":
    main()