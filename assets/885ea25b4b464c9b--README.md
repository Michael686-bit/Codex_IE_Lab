# GP001 宿主机直读

这里的脚本直接在宿主机打开 GP001 串口，SynthNova 仅作为现有厂商交付包的来源；脚本不会进入容器，也不会连接或控制真机机器人。

## 1. 安全预检

预检不会导入 `remote_control_lite`，也不会打开串口：

```bash
./run_gp001_host.sh --check-only
```

准备完成时，输出中的 `ready_for_capture` 应为 `true`。串口通常属于 `dialout` 组；持久修复方式是把当前用户加入该组，然后注销并重新登录：

```bash
sudo usermod -aG dialout "$USER"
```

不要用长期 `chmod 666 /dev/ttyACM0` 代替设备组权限。

预检还会用 `fuser` 检查当前打开串口的进程；这只能反映检查瞬间，并可能受进程权限或 PID 命名空间限制，无法消除检查后 `ModemManager` 或其他程序抢占设备的竞态。如果实际读取不稳定，应先处理该服务或为此 VID/PID 配置忽略规则。

## 2. 授权环境

真实导入需要厂商提供的联网授权变量。不要把值写进脚本、README、命令历史或 JSONL：

```bash
read -r -p 'ENCMGR_APP_ID: ' ENCMGR_APP_ID
read -r -s -p 'ENCMGR_APP_SECRET: ' ENCMGR_APP_SECRET
printf '\n'
export ENCMGR_APP_ID ENCMGR_APP_SECRET
```

如果凭据曾被明文记录，应先在厂商授权系统轮换。

## 3. 首次有界采集

`GalbotDriver` 可能向 GP001 发送握手、启动流或配置数据，因此真实运行必须显式确认这一点。真实硬件采集必须保留外层看门狗：厂商原生扩展若卡在初始化或关闭中，Python 内部时限无法强制打断它。

```bash
timeout --signal=INT --kill-after=3s 15s \
  ./run_gp001_host.sh \
  --ack-driver-may-write \
  --port /dev/serial/by-id/usb-Galbot_Galbot_Remote_Operate_ComPort_206F33685052-if00 \
  --duration-s 10 \
  --max-frames 100 \
  --print-frames
```

未指定 `--output` 时，新日志会以排他创建方式写入当前目录的 `captures/`，不会覆盖已有文件。

每个有效帧保存以下信息：

- 设备原始 `timestamp`，单位保持 `unknown`，不解释为电脑日期时间；
- 左右臂各 7 个 `position`，单位保持 `unknown`；
- `time.time_ns()` 和 `time.monotonic_ns()`；
- 时间打点位置 `queue_dequeue`，即主线程从队列取出一帧的时刻，并非串口字节到达内核的精确时刻。

JSONL 同时包含 `session_start`、`frame`、`diagnostic` 和 `session_end` 记录。脚本逐帧消费和保存，不主动排空或跳过中间帧。队列的厂商溢出策略没有公开说明，因此 `queue_drops` 明确记录为 `null`，不能把它解释成零丢帧。

## 4. 本地测试

以下测试不需要设备或厂商包：

```bash
python3 -B test_gp001_capture.py
```