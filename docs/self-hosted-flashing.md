# Flash NeoCam from a successful GitHub build

The **NeoCam flash** workflow is started manually with `workflow_dispatch` on
`main`. It takes an existing successful **NeoCam integration** build on `main`,
downloads its firmware artifact, and flashes the USB-connected board on your
Ubuntu machine. It does not fetch modules or compile firmware again.

```text
neocam_csw: NeoCam integration (GitHub-hosted Ubuntu + ESP-IDF container)
    -> successful main run -> firmware-esp32s3-<run_id> artifact
    -> NeoCam flash: select build (GitHub-hosted Ubuntu)
    -> NeoCam flash: download / flash / verify / timed monitor (your Ubuntu + USB ESP32-S3)
    -> hardware-flash-<run_id>-<attempt> report and serial-log artifact
```

The product caller is `.github/workflows/flash.yml`. Its shared orchestration is
`NeoTech-vietnam/ci-workflows/.github/workflows/flash-esp32.yml@v1.2.0`.
Product checks and the esptool command live in `TOOLCONF/hardware_flash.py`.
The automatic `GITHUB_TOKEN` has `contents: read` and `actions: read` in this
repository. There is no additional PAT or `PACKAGE_READ_TOKEN` needed to flash.

The current hardware target is the project's **XIAO ESP32-S3 Sense / OV3660**
configuration, with **8 MB DIO flash at 80 MHz** and octal PSRAM. The script checks
the generated firmware manifest against that configuration. An ESP32-C3/C6 or a
different ESP32-S3 board configuration is not an interchangeable target.

## 1. Prepare Ubuntu and USB access

Use Ubuntu 22.04 or 24.04, a normal user account with sudo access, and a USB data
cable. Keep this machine powered on and connected to the Internet for jobs.
The board must be connected to this machine, not your Windows computer.

Run in an Ubuntu Bash terminal as the account that will run Actions:

```bash
sudo apt update
sudo apt install -y curl ca-certificates git python3 python3-venv python3-pip
sudo usermod -aG dialout "$USER"
```

**Log out and log back in**, then check that `dialout` appears:

```bash
id -nG
```

Close serial monitors that currently hold the board port. Plug in the board and
list its stable USB identity:

```bash
ls -l /dev/serial/by-id/
```

Unplug/replug the intended board to identify its entry. Copy its complete path,
for example `/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_<YOUR-ID>-if00`.
Use your board's actual identity; the SPI example's device serial is not yours.
If the board only exposes `/dev/ttyACM0` or `/dev/ttyUSB0`, that explicit path also
works, but its number can change after reconnecting another device.

Check your selected device (replace the example path):

```bash
BOARD_PORT='/dev/serial/by-id/REPLACE_WITH_YOUR_DEVICE'
readlink -f "$BOARD_PORT"
test -c "$BOARD_PORT" && test -r "$BOARD_PORT" && test -w "$BOARD_PORT" && echo 'Serial access OK'
```

The resolved path must be `/dev/ttyACM<number>` or `/dev/ttyUSB<number>`.
If the device is absent, check the USB cable and board boot mode before proceeding.

## 2. Install the flashing environment

No full ESP-IDF installation or Docker is needed on this runner. Build outputs
already contain everything to flash. Create the environment under the same user's
home; the workflow looks for this exact location:

```bash
python3 -m venv "$HOME/.venvs/neocam-flash"
"$HOME/.venvs/neocam-flash/bin/python" -m pip install 'esptool==5.6.0' 'esp-idf-monitor==1.11.0'
"$HOME/.venvs/neocam-flash/bin/python" -m esptool version
```

The version check does not write to the board. The workflow installs the pinned
esptool 5.6.0 and IDF Monitor 1.11.0 from `TOOLCONF/requirements-flash.txt` before
flashing. An existing configured runner needs no manual environment update; its
next job installs the added monitor package automatically.

## 3. Download and register the Actions runner

Open [neocam_csw → Settings → Actions → Runners → New self-hosted runner](https://github.com/NeoTech-vietnam/neocam_csw/settings/actions/runners/new).
Choose **Linux** and the architecture matching `uname -m`:
`x86_64` means **x64**, `aarch64` means **ARM64**.

Use a dedicated runner installation even if your SPI examples already use another
runner. In the Ubuntu terminal:

```bash
mkdir -p "$HOME/actions-runner-neocam"
cd "$HOME/actions-runner-neocam"
uname -m
```

Run GitHub's current **download**, **checksum verification** and **extraction**
commands from that page in this directory. Skip its `mkdir actions-runner` / `cd
actions-runner` lines because you already created your dedicated directory. The
version and download URL on the page are the authority; do not reuse an old URL.

Instead of pasting a registration token into shell history, copy the token shown
in GitHub's `./config.sh` command and enter it at this hidden prompt:

```bash
read -r -s -p 'GitHub runner registration token: ' RUNNER_TOKEN
echo
./config.sh --unattended \
  --url https://github.com/NeoTech-vietnam/neocam_csw \
  --token "$RUNNER_TOKEN" \
  --name neocam-ubuntu \
  --labels neocam-flash \
  --work _work
unset RUNNER_TOKEN
```

The registration token expires after one hour; refresh the GitHub page if needed.
Use the short-lived **runner registration token**, not the package-read PAT.
Do not run `config.sh` with sudo. If it reports missing OS dependencies, run
`sudo ./bin/installdependencies.sh` and retry configuration.

Keep the default labels. The flash job matches **self-hosted**, **Linux**, and
**neocam-flash**. Assign `neocam-flash` only to the runner attached to this board.
Register this runner to the private `neocam_csw` repository; normal build/PR jobs
continue to use GitHub-hosted Ubuntu.

## 4. Start it as a service

From the runner directory, after group membership has taken effect:

```bash
cd "$HOME/actions-runner-neocam"
sudo ./svc.sh install "$(whoami)"
sudo ./svc.sh start
sudo ./svc.sh status
```

Do not also start `./run.sh` while its service is running. The service runs as your
normal user and starts after reboot. The GitHub Runners page should now show
**neocam-ubuntu — Idle** with the required labels.

## 5. Set the board port on GitHub

Open [neocam_csw → Settings → Secrets and variables → Actions → Variables](https://github.com/NeoTech-vietnam/neocam_csw/settings/variables/actions).

Choose **New repository variable**:

| Field | Value |
| --- | --- |
| Name | `NEOCAM_SERIAL_PORT` |
| Value | The complete `/dev/serial/by-id/...` path you checked in step 1 |

This is a **variable**, not a secret. Its value identifies the attached board;
no password or package credential belongs here. The workflow refuses to queue a
hardware job if it is empty. Do not put a Windows `COM` port here.

## 6. Choose the successful firmware

Open [NeoCam integration runs](https://github.com/NeoTech-vietnam/neocam_csw/actions/workflows/integration.yml).
Choose a green, completed run on **main**. Its artifact must still be available;
firmware artifacts currently expire after **seven days**. If necessary, run the
integration workflow again on main and wait for success.

The run ID is the number at the end of its URL. For example, the first verified
product build was `44980237440`:
`https://github.com/NeoTech-vietnam/neocam_csw/actions/runs/44980237440`.
Use that only while its artifact remains available.

An empty source ID selects the latest successful eligible main integration run
when the selection job starts. The selected ID and commit are then fixed for that
flash. An explicit ID is useful for repeatability or flashing an older baseline.
Feature-branch, PR, unsuccessful, wrong-workflow and expired-artifact selections
are rejected. A successful manually dispatched main build with a package override
is eligible; consult its resolved module SHAs when choosing your firmware.

## 7. Dispatch the flash

1. Verify the correct board is connected, serial monitors are closed, and the
   Ubuntu runner is **Idle**.
2. Open [Actions → NeoCam flash](https://github.com/NeoTech-vietnam/neocam_csw/actions/workflows/flash.yml).
3. Choose **Run workflow** and select branch **main**.
4. Set **source_run_id** to the successful integration run ID, or leave it empty.
5. Leave **baud** at `460800` initially. Use `115200` if the serial link is unreliable.
6. Leave **monitor_seconds** at `30` for a short capture, choose up to `300`, or
   select `0` to skip monitoring. Leave **monitor_baud** at `115200`, which matches
   the firmware console. Flashing baud and monitor baud are separate settings.
7. Click **Run workflow**. This starts the hardware write without further prompts.

The hosted `select` job verifies the source. The self-hosted `flash` job downloads
the frozen artifact, checks its binaries, calls esptool to write/verify them, and
resets the board. The **Monitor ESP32-S3 serial output** step then opens the same
port with Espressif's IDF Monitor, resets once to capture a fresh boot, and streams
timestamped serial output into the Actions log for the chosen duration. It exits
normally after that capture, releasing the serial port. Jobs for this board are
serialized across both flashing and monitoring; starting another run does
not cancel an active flash. GitHub concurrency may replace an older pending job
when several dispatches are queued, so dispatch one board run at a time.

The workflow writes the generated bootloader at `0x0`, partition table at
`0x8000`, and application at `0x10000`. It does not perform a whole-chip erase;
ordinary flashing keeps existing NVS data outside the written regions. Successful
write/verification does not by itself prove camera/Wi-Fi behavior. The timed serial
capture provides logs for inspection; it does not fail on application panic text
or assert camera/Wi-Fi health. Monitor connection/process failures still fail the
step. A watchdog allows 30 extra seconds for connection/shutdown and reports a
failure if the process does not finish. With native USB, logs are exposed through
the firmware's enabled secondary USB Serial/JTAG console.

This is a CI capture session. The Actions page displays output; interactive
keyboard shortcuts and commands are available when you run `idf.py monitor`
locally. Address, panic and core-dump decoding are disabled in this standalone
capture, so the Ubuntu flashing runner needs no cross-toolchain. Raw diagnostic
output remains in the log.

## 8. Inspect the result or diagnose a failure

The selection job summary links the chosen build and its exact project commit.
The flash run uploads `hardware-flash-<flash-run-id>-<attempt>` containing the
esptool log and JSON provenance: source run/commit, port, baud and binary SHA-256
hashes. `flashed-and-verified` means esptool completed successfully. Keep these
reports separate from camera/runtime acceptance evidence. When monitoring is
enabled, the same artifact also includes **`serial-monitor.log`**. You can watch
that output live by expanding **Monitor ESP32-S3 serial output** in the run, or
download the artifact after it finishes. The log is retained even if monitoring
fails after producing partial output. With duration `0`, no serial log is created.

| Symptom | Check |
| --- | --- |
| Missing `NEOCAM_SERIAL_PORT` | Add the repository **variable** from step 5 |
| Waiting for runner | Ubuntu machine online, service running, labels match; cancel stale queued runs before leaving the board unattended |
| Permission denied | Runner service user belongs to `dialout`; restart the service after group changes using `sudo ./svc.sh stop` then `sudo ./svc.sh start` |
| Port absent | Cable, stable path, board power; re-list `/dev/serial/by-id/` |
| Port busy | Close ESP-IDF/Arduino/other serial monitors; use `fuser "$BOARD_PORT"` to identify the holder |
| Failed to connect | Hold BOOT, press/release RESET, release BOOT; recheck the serial path, then dispatch again |
| Wrong chip | Connect the configured ESP32-S3 board; do not bypass chip checks |
| Missing/expired artifact | Rebuild NeoCam integration on main, then select the new successful run |
| Serial transfer errors | Try baud `115200` and a better USB data cable |
| Unreadable monitor text | Set **monitor_baud** to the firmware console rate, currently `115200` |
| Monitor watchdog timeout | Check USB reconnect/port identity; the timed capture should exit normally without timing out |

An offline matching runner can leave a job queued for up to 24 hours. Cancelling
a queued job is safe; avoid interrupting an active flash or removing board power.
If interrupted, reconnect the board in download mode and flash the complete
artifact again. USB identities can differ between application and download modes;
check your stable path after changing modes.

## Hardware-free validation for maintainers

```bash
python test/test_hardware_flash.py
python TOOLCONF/hardware_flash.py flash \
  --artifact-root /path/to/extracted/firmware-artifact \
  --port /dev/serial/by-id/EXAMPLE \
  --report _out/hardware-flash-dry-run.json
```

Omitting `--execute` validates the artifact, prints the command and writes a
dry-run report without opening a serial port. Firmware is treated as data;
the runner uses checked-out main tools, never scripts from the artifact.

After installing the pinned flashing requirements, IDF Monitor's headless mode
can also be checked without a board using pyserial's in-memory loopback port:

```bash
printf 'send NeoCam monitor smoke\nsleep 0.5\n' | \
  "$HOME/.venvs/neocam-flash/bin/python" -u -m esp_idf_monitor \
    --port loop:// --baud 115200 --target esp32s3 --timestamps \
    --disable-auto-color --disable-address-decoding \
    --decode-coredumps disable --decode-panic disable
```

Expected: a timestamped `NeoCam monitor smoke` line and exit code 0 after the
short capture. Without an ELF argument, this smoke check prints a harmless
missing-ELF warning. CI supplies the selected artifact's ELF file.

## References and SPI example mapping

- The [SPI validation Makefile](https://github.com/NeoTech-vietnam/NeoExamples-ESP32-FreeRTOS/blob/feature/spi/03_Interfaces-and-Protocols/01_Basic/03_SPI/00_validate_project/Makefile)
  separates build/flash/monitor and checks stable Linux serial identities before
  flashing. NeoCam follows that port-selection behavior and uses existing CI
  binaries instead of rebuilding with `idf.py flash`. SPI LCD wiring is unrelated
  to NeoCam's camera target and is not copied.
- [Espressif: flash prebuilt firmware](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/flashing-firmware.html).
- [Espressif: IDF Monitor command-stream mode](https://github.com/espressif/esp-idf-monitor/tree/v1.11.0#command-stream-mode).
- [Espressif: serial access and boot mode](https://docs.espressif.com/projects/esp-idf/en/v6.0.1/esp32s3/get-started/establish-serial-connection.html).
- [GitHub: add a self-hosted runner](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).
- [GitHub: run the runner as a service](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application).
- [GitHub: download artifacts from another run](https://github.com/actions/download-artifact/tree/v4).
