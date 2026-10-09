# 2026-07-26 — Airflow down after EC2 reboot: `/tmp` key mount fix + disk audit

## TL;DR

`platform.datap.ai` rebooted **Fri 2026-07-24 02:54 UTC**. The reboot wiped `/tmp`,
which is where the Snowflake key `/tmp/airbyte_user.p8` lived. The Airflow compose
bind-mounts that file into every service. With the source gone, Docker recreated
`/tmp/airbyte_user.p8` as an **empty directory** and then failed to mount a directory
onto a file target → **exit 127** on webserver/scheduler/triggerer. Airflow UI was
down for ~2 days. **Not a disk problem.** Fixed by repointing the mount at a
reboot-persistent key path. Airbyte was never affected.

## Symptom → why → fix

| | |
|---|---|
| **Symptom** | `airflow.datap.ai` unreachable; all 3 Airflow containers `Exited (127)` since Jul 24 02:54. |
| **Why** | EC2 rebooted → Linux clears `/tmp` on boot → `/tmp/airbyte_user.p8` (the mount source) vanished → Docker auto-created it as an empty **directory** → OCI runtime error: `not a directory: Are you trying to mount a directory onto a file?` → exit 127. `restart: unless-stopped` made it retry-and-fail in a loop. |
| **Fix** | Removed the empty `/tmp` dir, repointed the compose mount to the persistent copy `/home/ec2-user/.snowflake-keys/airbyte_user.p8`, granted container (gid 0) read access, recreated the stack. |

## Root-cause evidence

- `docker inspect dbt_airflow-airflow-scheduler-1` exit info:
  ```
  exited exit=127 err=failed to create shim task: OCI runtime create failed:
  error mounting "/tmp/airbyte_user.p8" to rootfs at "/snowflake-keys/airbyte_user.p8":
  not a directory: Are you trying to mount a directory onto a file (or vice-versa)?
  ```
- `/tmp/airbyte_user.p8` was a `directory drwxr-xr-x root`, created `Jul 24 02:54` (reboot time).
- Nothing repopulates `/tmp/airbyte_user.p8` on boot — no `.bash_profile`, systemd unit, or `rc.local` entry. It was placed manually once and only survived until the next reboot.
- The container's own baked-in `/snowflake-keys/airbyte_user.p8` is a **0-byte** file (empty-file sha256). The only valid key is `/home/ec2-user/.snowflake-keys/airbyte_user.p8` (1708 bytes).

## Changes made (all on EC2 `platform.datap.ai`)

File: `/home/ec2-user/git/datapai-airflow/dbt_airflow/docker-compose.datapai.yml`
(backup: `docker-compose.datapai.yml.bak-20260726`)

- **Line 32** mount changed:
  - before: `- /tmp/airbyte_user.p8:/snowflake-keys/airbyte_user.p8:ro`
  - after:  `- /home/ec2-user/.snowflake-keys/airbyte_user.p8:/snowflake-keys/airbyte_user.p8:ro`
- Key perms: `chgrp 0 && chmod 640` on `/home/ec2-user/.snowflake-keys/airbyte_user.p8`
  (was `0600 ec2-user:ec2-user` → now `0640 ec2-user:root`). Airflow runs as
  `uid 50000, gid 0` inside the container, so group-0 read is the minimal grant that
  lets dbt/Snowflake DAGs read the key. Tighter than the old world-readable `/tmp` copy.
- `rmdir /tmp/airbyte_user.p8` (removed the bogus empty dir Docker created).
- `docker compose -f docker-compose.datapai.yml up -d` (run as `ec2-user`, who is in the
  `docker` group — **do NOT use `sudo docker compose`**, the v2 plugin isn't on root's PATH,
  only `docker-buildx` is in `/usr/libexec/docker/cli-plugins/`).

## Why this is now reboot-proof

The mount source lives under `/home` (persistent EBS), not `/tmp`. `restart: unless-stopped`
will bring the stack back automatically when the Docker daemon starts after any future boot.
Key perms persist across reboots.

## Verification

```
docker ps           → all 3 airflow services "Up"
curl :8180/health   → HTTP 200; metadatabase/scheduler/triggerer "healthy"
curl :8180/login/   → HTTP 200
docker exec scheduler head -c40 /snowflake-keys/airbyte_user.p8 → "-----BEGIN PRIVATE KEY-----" (readable)
scheduler logs      → already draining the 2-day task backlog (parallelism limit reached = normal catch-up)
```

## Disk audit (separate issue — NOT the cause; left untouched per user)

Root `/dev/nvme0n1p1` = **150G, 120G used, 80%** at time of audit (was likely ~97% pre-reboot).
Owner is Docker: `/var/lib/docker/overlay2` 79G + `volumes` 25G (biggest volume =
`datapai_stock_db_data` 13G, legit data). `/var/log/journal` = 4.1G.

`docker system df`: ~5.5G dangling images + 0.85G build cache + 0.7G dead containers reclaimable,
plus ~3.6G journald vacuum ≈ **~11G safely reclaimable**.

**User decision (2026-07-26): do NOT prune images/data — add EBS capacity instead.**
So no cleanup was performed. Next step when convenient: grow the EBS volume + `growpart` +
`resize2fs` (or `xfs_growfs`). This is a separate infra task requiring AWS console access.

## Pending

- [ ] Grow EBS volume (disk at 80% and climbing) — user opted for capacity over cleanup.
- [ ] Pull the compose edit back to the local `datapai-airflow` repo and commit (EC2 is source of truth).
