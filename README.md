# ALEX-SENDER — home server dashboard

A tiny ASCII-styled web dashboard for a Raspberry Pi 5 home server:
CPU usage/temp, RAM usage, uptime in one panel; SSD (boot) and HDD
(WD My Book) storage usage in the other. Auto-refreshes every 3s.

## 1. Get the files onto the Pi

Copy this whole `alex-sender/` folder to the Pi, e.g. with `scp`:

```bash
scp -r alex-sender pi@<pi-ip-address>:/home/pi/
```

Or `git clone` if you push it to a repo first.

## 2. Mount the WD My Book permanently

Plug it in, find its device name, and add it to `/etc/fstab` so it's
always mounted at the same path (adjust `/mnt/storage` to taste — just
match `HDD_MOUNT` in `app.py` afterwards):

```bash
lsblk -f                     # find the device, e.g. /dev/sda1, and its UUID
sudo mkdir -p /mnt/storage
sudo blkid /dev/sda1         # copy the UUID
sudo nano /etc/fstab
```

Add a line like (replace UUID and filesystem type as needed):

```
UUID=XXXX-XXXX  /mnt/storage  ext4  defaults,auto,nofail  0  2
```

Then:

```bash
sudo mount -a                # mounts it now; also verifies fstab syntax
```

## 3. Install dependencies

Raspberry Pi OS (Bookworm) blocks system-wide `pip install`, so use a
virtual environment:

```bash
cd /home/pi/alex-sender
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Set the HDD mount path

Open `app.py` and confirm `HDD_MOUNT` matches step 2's mount point
(default is `/mnt/storage`).

## 5. Test it manually

```bash
source venv/bin/activate
python3 app.py
```

Visit `http://<pi-ip-address>:5000` from any device on your network.
Stop with Ctrl+C once you've confirmed it works.

## 6. Run it as a service (auto-start on boot)

```bash
sudo cp alex-sender.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now alex-sender.service
```

Check status / logs:

```bash
sudo systemctl status alex-sender
journalctl -u alex-sender -f
```

## 7. Optional: actually rename the Pi to alex-sender

This only changes the hostname (what the Pi calls itself on the
network) — separate from the `SERVER_NAME` label shown on the
dashboard, which is already set to `ALEX-SENDER` in `app.py`.

```bash
sudo raspi-config   # System Options -> Hostname -> alex-sender
sudo reboot
```

After that you can reach the dashboard at `http://alex-sender.local:5000`
too (via mDNS), instead of typing the IP.

## Notes

- CPU temperature is read from `/sys/class/thermal/thermal_zone0/temp`,
  which is standard on Raspberry Pi OS — no extra setup needed.
- If the HDD panel shows "not mounted", double check `HDD_MOUNT` in
  `app.py` against `df -h` output on the Pi.
- Port 5000 is only reachable on your local network by default. If you
  ever expose it beyond that, put it behind auth/reverse proxy first.
