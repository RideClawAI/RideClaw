***

name: lobster_ride
description: A command-line interface tool for ride-hailing service. Provides CLI commands to initialize user profile (home/company address, phone), search locations, estimate prices, pay and create ride orders, query order and driver status, and cancel rides. Use when users need to book a taxi via command line or interact with the Lobster Ride platform.

***

# 龙虾出行 CLI

龙虾出行命令行打车工具，支持全流程打车服务。

首次加载时向用户展示以下欢迎信息：

```text
已安装rideclaw skill，这个skill可以为您便捷打车。

- 自然语言交互：支持"打车去公司"、"帮我叫辆便宜的车"等口语化指令
- 多平台呼叫：聚合主流打车平台，一键全网呼叫
- 智能估价与预估：实时同步各车型价格、行驶里程及预计到达时间
- 常用地址记忆：支持预设"家/公司"地址，实现秒级发单

为了确保正常叫车，请先告诉我用车人手机号：
```

## 核心流程

1. **搜索起终点** → `location-search` 获取坐标
2. **确认地点** → 展示给用户确认
3. **预估价格** → `estimate` 获取车型和价格，默认推荐特惠快车
4. **用户确认车型** → 等待用户确认后继续
5. **支付下单（Agent 自动链式执行）**：
   - 调用 `pay` → 展示支付链接
   - 每 5s 轮询 `pay-status` → 反馈"等待支付中..."，直到 `pay_status == 2`
   - 每 5s 轮询 `query-order` → 反馈"匹配司机中..."，直到返回含 `driver`
   - 每 10s 轮询 `driver-location` → 播报行程动态，直到"行程已完成"

## 命令参考

### location-search

搜索地点，获取坐标。

```bash
python scripts/lobster_cli.py location-search --keywords "北京西站" --city "北京"
```

### estimate

预估价格，返回可选车型和 `estimate_trace_id`。

```bash
python scripts/lobster_cli.py estimate \
  --from-lng "116.404" --from-lat "39.877" --from-name "永定门桥" \
  --to-lng "116.655" --to-lat "39.854" --to-name "文景东街"
```

### pay

生成支付订单，立即返回支付链接和订单号。

```bash
python scripts/lobster_cli.py pay \
  --estimate-trace-id "xxx" \
  --from-lng "116.404" --from-lat "39.877" --from-name "永定门桥" \
  --to-lng "116.655" --to-lat "39.854" --to-name "文景东街" \
  --product-category "201" --product-name "特惠快车" --estimate-price 1000
```

**Agent 执行流程：**
1. 调用 `pay` → 立即展示支付链接
2. 每 5s 调用 `pay-status` → `pay_status == 2` 时停止，告知"支付成功"
3. 每 5s 调用 `query-order` → 返回含 `driver` 时停止，告知司机信息
4. 每 10s 调用 `driver-location` → 返回含"行程已完成"语义时停止

### pay-status

单次查询支付状态。Agent 每 5s 轮询。

```bash
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
```

**判断：** `pay_status == 2` → 支付成功

### query-order

单次查询订单状态。Agent 每 5s 轮询。

```bash
python scripts/lobster_cli.py query-order --order-no "RC20260324405660"
```

**判断：** 返回含 `driver` 字段 → 司机已接单

### driver-location

单次获取司机位置与行程动态。Agent 每 10s 轮询。

```bash
python scripts/lobster_cli.py driver-location --order-id "2j08KLO61gHGsc"
```

**判断：** 返回含"行程已完成"/"已到达目的地"语义 → 行程结束

### cancel-order

取消订单。

```bash
python scripts/lobster_cli.py cancel-order --order-id "2j08KLO61gHGsc"
```

### order-detail

查询订单完整详情。

```bash
python scripts/lobster_cli.py order-detail --order-no "RC20260324405660"
```

## 订单状态说明

| 状态 | 含义 | Agent 动作 |
|------|------|-----------|
| 待支付 | 等待用户支付 | 轮询 `pay-status` |
| 支付成功 | 支付完成，后台创建订单 | 开始轮询 `query-order` |
| 呼叫中 | 等待司机接单 | 继续轮询 `query-order` |
| 司机已接单 | 司机接单 | 开始轮询 `driver-location` |
| 履约中 | 行程进行中 | 继续轮询 `driver-location` |
| 行程已完成 | 行程结束 | 停止轮询 |

**关键：**
- "支付成功" ≠ 打车完成，必须继续轮询直到"行程已完成"
- 所有命令都是单次查询立即返回，由 Agent 控制轮询节奏

## Notes

- 所有命令支持 `--json` 输出 JSON 格式
- 坐标格式为字符串（如 "116.397128"）
