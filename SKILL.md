---
name: rideclaw
description: A command-line interface tool for ride-hailing service. Provides CLI commands to initialize user profile (home/company address, phone), search locations, estimate prices, pay and create ride orders, query order and driver status, and cancel rides. Use when users need to book a taxi via command line or interact with the Lobster Ride platform.
---

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
   - **之后只需执行每条命令输出末尾的 `NEXT_ACTION` 指令即可**，无需记忆完整流程

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

**输出末尾包含 `NEXT_ACTION` 指令，Agent 只需执行该指令即可。**

### pay-status

查询支付状态。

```bash
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
```

**输出末尾包含 `NEXT_ACTION` 指令，Agent 只需执行该指令即可。**

### query-order

查询订单状态。

```bash
python scripts/lobster_cli.py query-order --order-no "RC20260324405660"
```

**输出末尾包含 `NEXT_ACTION` 指令，Agent 只需执行该指令即可。**

### driver-location

获取司机位置与行程动态。

```bash
python scripts/lobster_cli.py driver-location --order-id "2j08KLO61gHGsc"
```

**输出末尾包含 `NEXT_ACTION` 指令，Agent 只需执行该指令即可。当输出 `NEXT_ACTION: DONE` 时表示行程结束。**

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

所有命令输出末尾都包含 `NEXT_ACTION` 指令，Agent 只需执行该指令即可自动完成状态流转：

- 待支付 → 轮询 `pay-status`
- 支付成功 → 转到 `query-order`
- 呼叫中 → 轮询 `query-order`
- 司机已接单 → 转到 `driver-location`
- 履约中 → 轮询 `driver-location`
- 行程已完成 → `NEXT_ACTION: DONE`

**关键：Agent 无需记忆完整流程，只需执行上一条输出的 `NEXT_ACTION` 即可。**

## Notes

- 所有命令支持 `--json` 输出 JSON 格式
- 坐标格式为字符串（如 "116.397128"）
