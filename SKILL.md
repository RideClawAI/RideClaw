***

name: rideclaw
description: A command-line interface tool for ride-hailing service. Provides CLI commands to initialize user profile (home/company address, phone), search locations, estimate prices, pay and create ride orders, query order and driver status, and cancel rides. Use when users need to book a taxi via command line or interact with the Lobster Ride platform.
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# 龙虾出行 CLI -v0.1.1

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
   - 调用 `pay-status` → 查询一次支付状态
   - Agent 不做自动连续轮询，等用户反馈
6. **支付成功后（重要）**：
   - 当 `pay-status` 返回支付成功（pay\_status=2）后，**必须切换**到 `query-order` 或 `driver-location` 查询订单进展
   - **严禁**在支付成功后继续重复调用 `pay-status`，该命令仅用于确认支付是否完成
   - 用户后续发送"查询"类消息时，应调用 `query-order` 或 `driver-location`，而不是 `pay-status`

## 状态转换规则（Agent 必须遵守）

```
pay → pay-status（确认支付）
                ↓ 支付成功（pay_status=2）
          query-order / driver-location（查看司机和行程）
                ↓ 司机已接单
          driver-location（持续跟踪行程）
```

- `pay-status` 的职责：**仅确认是否已支付**。一旦确认支付成功，后续所有查询都应使用 `query-order` 或 `driver-location`
- 如果用户说"查一下订单"、"司机到哪了"、"什么状态了"，在支付成功后，都应调用 `query-order` 而非 `pay-status`
- `pay-status` 现在也会返回司机信息（如果有），Agent 应读取并告知用户

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

生成支付订单并立即返回支付链接。Agent 必须先将支付链接发送给用户，然后再通过 `pay-status` 查询支付状态。

```bash
python scripts/lobster_cli.py pay \
  --estimate-trace-id "0a88bed669c260c39a8704fa9b41b1b0" \
  --from-lng "116.404000" --from-lat "39.877912" --from-name "永定门桥" \
  --to-lng "116.655885" --to-lat "39.854873" --to-name "文景东街" \
  --product-category "1" --product-name "快车" --estimate-price 1500 \
```

**Parameters:**

- `--estimate-trace-id, -e`: 预估流程 ID (required)
- `--from-lng / --from-lat / --from-name`: 出发地坐标和名称 (required)
- `--to-lng / --to-lat / --to-name`: 目的地坐标和名称 (required)
- `--product-category, -p`: 车型品类代码 (required)
- `--product-name`: 车型名称 (required)
- `--estimate-price`: 预估价格，单位分 (required)
- `--caller-car-phone`: 叫车人手机号 (optional, 默认从 profile 读取)

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

查询支付状态。支付成功后会同时返回司机信息和行程动态（如果已有），以及 `NEXT_ACTION` 指引。

```bash
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
```

**Output (支付成功，司机已接单):**

```text
PAY STATUS:
------------------------------------------------------------
  订单号:   RC20260324405660
  支付状态: 已支付 (Code: 2)
  订单状态: 已接单 (Code: 3)

✓ 支付成功！

  司机已接单：
    司机: 张师傅
    电话: 138****1234
    车辆: 丰田卡罗拉 (京A·12345)
    上车码: 1234

NEXT_ACTION: 支付已完成，请使用 query-order 或 driver-location 查询订单进展，不要再重复调用 pay-status。
```

**Output (支付成功，等待匹配司机):**

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
  支付状态: 待支付 (Code: 1)
  订单状态: 待支付 (Code: 1)

⚠ 未付款，等待用户支付中。
```

**Agent 调用规则（必须遵守）：**

1. 调用 `pay` → 拿到支付链接、订单号
2. **立即**将支付链接发送给用户
3. 调用 `pay-status --order-no xxx` 查询一次
4. **如果返回中包含** **`NEXT_ACTION`，表示支付已成功，后续查询必须切换到** **`query-order`** **或** **`driver-location`**
5. **严禁在支付成功后继续调用** **`pay-status`**
6. 如果未支付，等待用户反馈后再查询

### query-order

查询订单状态（支付成功后应使用此命令代替 pay-status）,如果有获取到行程动态，把行程动态也返回上。

```bash
python scripts/lobster_cli.py query-order --order-no "RC20260324405660"
```

**Parameters:**

- `--order-no, -o`: 订单号 (required)

**Output (匹配成功):**

```text
行程动态：
✨ 司机已接单！
司机正在赶往上车点，请准备出发。

  车辆信息: 丰田卡罗拉·京A·12345
  司机: 张师傅  
  电话: 138****1234
```
**Output (行程中):**

```text
🚕 行程正在进行中
  司机: 张师傅  
  电话: 138****1234
  行程动态：
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


**Agent 调用规则：**

- **支付成功后，这是默认的查询命令**，用于替代 pay-status
- 用户说"查询"、"什么情况了"、"到哪了"时，在支付完成后都应调用此命令
- 如果司机已接单，可进一步调用 `driver-location` 跟踪行程

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

1. `pay-status` 返回支付成功（含 NEXT\_ACTION）后，切换到 `query-order --order-no xxx`
2. 如果司机已接单，调用 `driver-location --order-id xxx` 跟踪行程
3. 当 `driver-location` 返回的内容包含行程已完成的语义时，停止轮询，告知用户行程结束

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

- 1-待支付：等待用户支付
- 2-已支付：可查询司机匹配状态
- 3-履约中：行程进行中，可查询司机位置和行程动态
- 4-已完成：行程结束
- 5-已取消：订单已取消
- 6-异常：订单异常

## Notes

- 所有命令支持 `--json` 输出 JSON 格式
- 坐标格式为字符串（如 "116.397128"）

