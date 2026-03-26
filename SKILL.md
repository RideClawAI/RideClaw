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

# 触发方式

当用户表达打车出行相关诉求时触发，典型用户话术示例如下：

- 我要打车
- 我要从【出发地】到【目的地】
- 帮我叫辆车去【地点】
- 我需要打车去【目的地】
- 预约一辆【时间】从【起点】到【终点】的车

## Available Commands

| Command           | Description                       |
| ----------------- | --------------------------------- |
| `location-search` | 搜索地点                              |
| `place-around`    | 周边 POI 搜索                         |
| `estimate`        | 预估价格和车型                           |
| `pay`             | 生成支付订单 → 等待用户付款 → 支付成功后后台自动创建打车订单 |
| `pay-status`      | 查询支付状态                            |
| `query-order`     | 查询订单状态（含订单状态、司机信息等）               |
| `driver-location` | 获取司机实时位置与行程动态                     |
| `cancel-order`    | 取消订单                              |
| `order-detail`    | 查询订单详情                            |

## 核心流程

1. **搜索起终点** → `location-search` 获取坐标
2. **确认地点** → 展示给用户确认
3. **预估价格** → `estimate` 获取车型和价格，默认推荐特惠快车
4. **用户确认车型** → 等待用户确认后继续
5. **支付下单**：
   - 调用 `pay` → 展示支付链接
   - 每次命令只返回当前状态
   - Agent 不做自动连续轮询

## 命令参考

### location-search

搜索地点，获取坐标。

```bash
python scripts/lobster_cli.py location-search --keywords "北京西站" --city "北京"
```

**Parameters:**

- `--keywords, -k`: 搜索关键词 (required)
- `--city, -c`: 城市名称 (required)

**Output:**

```text
🔍 请确认您的具体位置
匹配到多个相似地点，请选择最准确的一个：

1. 北京西站 - 北京市丰台区莲花池东路118号 (116.322,39.894)
2. 北京西站南广场 - 北京市丰台区莲花池东路 (116.321,39.893)
3. 北京西站北广场 - 北京市丰台区北蜂窝路 (116.323,39.897)

请确认序号，或输入更详细的地址重新搜索。
```


### estimate

预估价格，返回可选车型和 `estimate_trace_id`。

```bash
python scripts/lobster_cli.py estimate \
  --from-lng "116.404" --from-lat "39.877" --from-name "永定门桥" \
  --to-lng "116.655" --to-lat "39.854" --to-name "文景东街"
```

**Output (默认推荐，若用户无指定车型优先推荐特惠快车):**

```text
您的上车点是 永定门桥，为您规划前往 文景东街 的用车行程。

  车型推荐: 特惠快车
  预估价格: ¥10.00

如需查看更多车型，告诉我即可。确认用车请回复"确认"，我将为您生成支付链接。
```

**Output (用户要求查看更多车型):**

```text
已为您搜索到多种车型
从 永定门桥 前往 文景东街，各车型实时价格如下：

  车型        预估价格
  特惠快车    ¥10.00
  快车        ¥15.00
  专车        ¥30.00
  豪华车      ¥100.00

您想选哪个？请直接回复车型名称（如："选特惠快车"）。
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

生成支付订单并立即返回支付链接。Agent 必须先将支付链接发送给用户，然后再通过 `pay-status` 轮询支付状态。

```bash
python scripts/lobster_cli.py pay \
  --estimate-trace-id "0a88bed669c260c39a8704fa9b41b1b0" \
  --from-lng "116.404000" --from-lat "39.877912" --from-name "永定门桥" \
  --to-lng "116.655885" --to-lat "39.854873" --to-name "文景东街" \
  --product-category "1" --product-name "快车" --estimate-price 1500 \
  --no-wait
```

**Parameters:**

- `--estimate-trace-id, -e`: 预估流程 ID (required)
- `--from-lng / --from-lat / --from-name`: 出发地坐标和名称 (required)
- `--to-lng / --to-lat / --to-name`: 目的地坐标和名称 (required)
- `--product-category, -p`: 车型品类代码 (required)
- `--product-name`: 车型名称 (required)
- `--estimate-price`: 预估价格，单位分 (required)
- `--caller-car-phone`: 叫车人手机号 (optional, 默认从 profile 读取)
- `--no-wait`: 只生成订单立即返回，不轮询 (Agent 场景必须加)

**Output:**

```text
已为您生成支付订单。
您的上车点是 永定门桥，为您规划前往 文景东街 的用车行程。

  车型:     快车
  预估价格: ¥15.00
  订单号:   RC20260324405660
  支付链接: https://dudubashi.com/rideclaw?order_no=RC20260324405660&mweb_url=...

请点击上方链接完成支付，支付成功后系统将自动为您创建打车订单。
如果需要调整起终点或车型，随时和我说。
```

**Output (用户重新选择车型后):**

```text
已为您重新选择车型。
您的上车点是 永定门桥，为您规划前往 文景东街 的用车行程。

  车型:     特惠快车
  预估价格: ¥10.00
  订单号:   RC20260324405661
  支付链接: https://dudubashi.com/rideclaw?order_no=RC20260324405661&mweb_url=...

请点击上方链接完成支付，支付成功后系统将自动为您创建打车订单。
如果需要调整起终点或车型，随时和我说。
```

### pay-status

查询支付状态。

```bash
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
```

**Output (支付成功):**

```text
🚗 正在为您呼叫车辆
已成功支付并下发订单，正在为您匹配最优司机。

  路线: 永定门桥 ➜ 文景东街
  已支付: ¥15.00
  状态: 正在全网呼叫中...

提示：匹配成功后我会立即通知您。如需取消，请回复"取消呼叫"。
```

**Output (未支付):**

```text
PAY STATUS:
------------------------------------------------------------
  订单号:   RC20260324405660
  支付状态: 待支付
  订单状态: 待支付

提示: 支付尚未完成。如需查询最新状态，请再次发送消息。
如需取消订单，请直接回复'取消订单'。
```

**Agent 调用建议（避免阻塞用户输入）：**

1. 调用 `pay` → 拿到支付链接、订单号、金额
2. **立即**将支付链接发送给用户
3. 调用 `pay-status --order-no xxx `，
4. 告知用户可以随时取消订单或查询最新状态
5. 等待用户主动反馈（如"已支付"、"取消订单"、"查询订单"等）

### query-order

查询订单状态。

```bash
python scripts/lobster_cli.py query-order --order-no "RC20260324405660"
```

**Parameters:**

- `--order-no, -o`: 订单号 (required)

**Output (匹配成功):**

```text
✨ 司机已接单！
司机正在赶往上车点，请准备出发。

  车辆信息: 丰田卡罗拉·京A·12345
  司机: 张师傅
  电话: 138****1234
```

**Agent 调用建议：**
- 在支付成功后，查询一次订单状态即可
- 告知用户可以随时取消订单
- 后续由用户主动查询或通过其他方式获取状态更新

### driver-location

获取司机位置与行程动态。

```bash
python scripts/lobster_cli.py driver-location --order-id "2j08KLO61gHGsc"
```

**Parameters:**

- `--order-id, -o`: 订单 ID (required)

**Output (行程中):**

```text
🚕 行程正在进行中
  司机张师傅正在赶来接您
  当前距离您还有2.3公里，预计3分钟到达
  车辆信息：丰田卡罗拉 京A·12345
```

**Output (行程结束):**

```text
🏁 您已到达目的地！
  行程: 永定门桥 ➜ 文景东街
  感谢使用龙虾出行，祝您愉快！
```

**Agent 调用流程：**

1. `pay-status` 返回支付成功后，调用 `query-order --order-no xxx`，命令会阻塞等待司机接单
2. 命令返回后，将司机信息告知用户
3. 然后每隔 10s 调用 `driver-location --order-id xxx`，将行程动态返回给用户
4. 当 `driver-location` 返回的内容包含行程已完成的语义时，停止轮询，告知用户行程结束

### cancel-order

取消订单。

```bash
python scripts/lobster_cli.py cancel-order --order-id "2j08KLO61gHGsc"
```
**Output (取消成功):**

```text
🛑 行程已取消
已按您的要求取消当前行程。

  取消状态: 成功
  车牌号码: 粤BDX7553（王师傅）

提示：您可以随时对我说"重新打车"或告知新的目的地。
```

**Output (取消失败):**

```text
❌ 取消失败
很抱歉，当前行程无法取消。

  失败原因: 司机已到达上车点或行程已开启
  当前状态: 行程进行中
  车牌号码: 粤BDX7553（王师傅）

提示：如需协助，请直接联系司机或联系客服。
```

### order-detail

查询订单完整详情。

```bash
python scripts/lobster_cli.py order-detail --order-no "RC20260324405660"
```
**Output:**

```text
🏁 您已到达目的地，请确认账单：

  行程:     永定门桥 ➜ 文景东街
  下单时间: 2026-03-24 18:05:35
  车型:     快车
  预估价格: ¥15.00
  最终费用: ¥14.50
  司机:     张师傅 (丰田卡罗拉 京A·12345)
  电话:     138****1234

感谢使用龙虾出行，本次行程已圆满结束！
```

## 订单状态说明

- 待支付：等待用户支付
- 支付成功：可查询司机匹配状态
- 呼叫中：等待司机接单
- 司机已接单：可查询司机位置和行程动态
- 履约中：行程进行中
- 行程已完成：行程结束

## Notes

- 所有命令支持 `--json` 输出 JSON 格式
- 坐标格式为字符串（如 "116.397128"）
