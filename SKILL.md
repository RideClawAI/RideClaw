***

name: lobster\_ride
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
| `pay`             | 生成支付订单，立即返回支付链接                    |
| `pay-status`      | 单次查询支付状态（由 Agent 每 5s 轮询）          |
| `query-order`     | 单次查询订单状态（由 Agent 每 5s 轮询）          |
| `driver-location` | 单次获取司机位置与行程动态（由 Agent 每 10s 轮询）   |
| `cancel-order`    | 取消订单                              |
| `order-detail`    | 查询订单详情                            |

## Workflow

1. **搜索出发地**: `python scripts/lobster_cli.py location-search --keywords "出发地" --city "城市"`
2. **搜索目的地**: `python scripts/lobster_cli.py location-search --keywords "目的地" --city "城市"`
3. **确认上下车点（需要用户确认）**: Agent 将搜索到的出发地和目的地整理后展示给用户，等待用户确认无误后再继续。若用户要求修改，重新搜索对应地点。示例：
   ```text
   请确认您的行程信息：
     上车点: 北京西站 - 北京市丰台区莲花池东路118号 (116.322,39.894)
     下车点: 文景东街 - 北京市通州区文景东街 (116.655,39.854)
   确认无误请回复"确认"，如需修改请告诉我。
   ```
4. **预估价格**: 用户确认后，调用 `python scripts/lobster_cli.py estimate --from-lng ... --to-lng ...`
5. **支付下单（Agent 自动链式执行，不可拆分）**:
   - 5a. 调用 `pay` → 拿到支付链接和订单号 → 立即展示给用户
   - 5b. Agent 每 5s 调用 `pay-status --order-no xxx`，向用户反馈"等待支付中..."，直到 `pay_status == 2`（支付成功）
   - 5c. 支付成功后，Agent 每 5s 调用 `query-order --order-no xxx`，向用户反馈"正在匹配司机..."，直到返回中包含 `driver` 信息
   - 5d. 司机接单后，Agent 每 10s 调用 `driver-location --order-id xxx`，将行程动态告知用户，直到返回内容包含"行程已完成"语义

> **重要：步骤 4 必须等待用户确认后才能继续。步骤 5a → 5b → 5c → 5d 是一个连续自动执行的链路，每个命令都是单次查询立即返回，由 Agent 负责循环调用和状态判断，每次拿到结果后立即向用户反馈当前状态。**

## Command Reference

### Location Commands

#### location-search

搜索地点，获取名称和坐标。

```bash
python scripts/lobster_cli.py location-search \
  --keywords "北京西站" \
  --city "北京"
```

**Parameters:**

- `--keywords, -k`: 搜索关键词 (required)
- `--city, -c`: 城市名称 (required)

**Output:**

```text
🔍 请确认您的起始地/目的地：北京西站到北京南站
```

#### place-around

周边 POI 搜索。

```bash
python scripts/lobster_cli.py place-around \
  --location "116.322,39.894" \
  --keyword "餐厅" \
  --radius 500
```

### Ride Commands

#### estimate

预估价格，返回可选车型和预估流程 ID,若用户无指定使用哪种车型，默认优先用特惠快车

```bash
python scripts/lobster_cli.py estimate \
  --from-lng "116.404" \
  --from-lat "39.877" \
  --from-name "永定门桥" \
  --to-lng "116.655" \
  --to-lat "39.854" \
  --to-name "文景东街"
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

#### pay

生成支付订单并立即返回支付链接。**Agent 拿到输出后必须立即展示支付链接，然后自动开始轮询 `pay-status`，整个过程无需等待用户回复。**

```bash
python scripts/lobster_cli.py pay \
  --estimate-trace-id "0a88bed669c260c39a8704fa9b41b1b0" \
  --from-lng "116.404000" --from-lat "39.877912" --from-name "永定门桥" \
  --to-lng "116.655885" --to-lat "39.854873" --to-name "文景东街" \
  --product-category "1" --product-name "快车" --estimate-price 1500
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

拿到输出后，Agent 的执行流程如下（全程自动，不等待用户回复）：

1. **立即**将订单号、金额、支付链接展示给用户
2. **立即开始**每 5s 调用 `pay-status --order-no xxx`，每次向用户反馈"等待支付中..."
3. 当 `pay_status == 2` 时，告知用户"支付成功"，**立即开始**每 5s 调用 `query-order --order-no xxx`
4. 当返回包含 `driver` 信息时，告知用户司机信息，**立即开始**每 10s 调用 `driver-location --order-id xxx`

***

#### pay-status

单次查询当前支付状态，立即返回。**Agent 负责每 5s 循环调用此命令，并在每次返回后向用户反馈当前状态。**

当 `pay_status == 2` 时表示支付成功，Agent 应停止轮询并继续调用 `query-order`。

```bash
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
```

**Parameters:**

- `--order-no, -o`: 支付订单号 (required)

**判断逻辑：**
- `pay_status == 2` → 支付成功，停止轮询，继续下一步
- 其他值 → 未支付，向用户反馈"等待支付中..."，5s 后再次调用

**Output (支付成功):**

```text
🚗 正在为您呼叫车辆
已成功支付并下发订单，正在为您匹配最优司机。

  路线: 永定门桥 ➜ 文景东街
  已支付: ¥15.00
  状态: 正在全网呼叫中...

提示：匹配成功后我会立即通知您。如需取消，请回复"取消呼叫"。
```

**Agent 轮询伪代码：**

```
1. 调用 pay → 展示支付链接
2. loop (每 5s):
     调用 pay-status → 若 pay_status == 2 → break，告知用户"支付成功"
     否则 → 告知用户"等待支付中..."
3. loop (每 5s):
     调用 query-order → 若返回含 driver → break，告知用户司机信息
     否则 → 告知用户"正在匹配司机..."
4. loop (每 10s):
     调用 driver-location → 告知用户行程动态
     若返回含"行程已完成"语义 → break，告知用户行程结束
```

#### query-order

单次查询当前订单状态，立即返回。**Agent 负责每 5s 循环调用此命令，直到返回中包含 `driver` 信息（司机已接单）。**

```bash
python scripts/lobster_cli.py query-order \
  --order-no "RC20260324405660"
```

**Parameters:**

- `--order-no, -o`: 订单号 (required)

**判断逻辑：**
- 返回数据中 `driver` 字段有值 → 司机已接单，停止轮询，展示司机信息，继续下一步
- `driver` 为空 → 尚未匹配，向用户反馈"正在匹配司机..."，5s 后再次调用

**Output (匹配成功):**

```text
✨ 司机已接单！
司机正在赶往上车点，请准备出发。

  车辆信息: 丰田卡罗拉·京A·12345
  司机: 张师傅
  电话: 138****1234
```

***

#### driver-location

获取司机实时位置与行程动态（单次查询，立即返回）。**Agent 负责每 10s 循环调用此命令，直到返回内容包含"行程已完成"语义。**

```bash
python scripts/lobster_cli.py driver-location \
  --order-id "2j08KLO61gHGsc"
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

**Agent 调用流程（司机接单后立即开始）：**

1. Agent 每 10s 调用 `driver-location --order-id xxx`
2. 每次将行程动态告知用户
3. 当返回内容包含"行程已完成"/"已到达目的地"/"行程结束"语义时，停止轮询，告知用户行程结束

#### cancel-order

取消订单。

```bash
python scripts/lobster_cli.py cancel-order \
  --order-id "2j08KLO61gHGsc"
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

#### order-detail

查询订单完整详情（含最终费用、司机信息等）。

```bash
python scripts/lobster_cli.py order-detail \
  --order-no "RC20260324405660"
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

## Complete Workflow Example

```bash
# 1. 首次使用，初始化配置
python scripts/lobster_cli.py init
# 输入: 手机号=13800138000, 城市=北京, 家=望京SOHO, 公司=中关村软件园

# 2. 搜索出发地
python scripts/lobster_cli.py location-search --keywords "永定门桥" --city "北京"
# 记录坐标: 116.404,39.877

# 3. 搜索目的地
python scripts/lobster_cli.py location-search --keywords "文景东街" --city "北京"
# 记录坐标: 116.655,39.854

# 4. 预估价格，选择车型
python scripts/lobster_cli.py estimate \
  --from-lng "116.404" --from-lat "39.877" --from-name "永定门桥" \
  --to-lng "116.655" --to-lat "39.854" --to-name "文景东街"
# 记录 product_category 和 estimate_trace_id

# 5. 支付（Agent 自动链式执行 5a→5b→5c→5d，不等待用户输入）
# 5a. 生成支付链接
python scripts/lobster_cli.py pay \
  --estimate-trace-id "0a88bed669c260c39a8704fa9b41b1b0" \
  --from-lng "116.404" --from-lat "39.877" --from-name "永定门桥" \
  --to-lng "116.655" --to-lat "39.854" --to-name "文景东街" \
  --product-category "201" --product-name "特惠快车" --estimate-price 1000
# → 立即展示支付链接给用户

# 5b. Agent 每 5s 轮询支付状态（无需用户确认）
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
# → pay_status == 2 时支付成功，继续下一步

# 5c. Agent 每 5s 轮询订单状态（支付成功后立即开始）
python scripts/lobster_cli.py query-order --order-no "RC20260324405660"
# → 返回含 driver 信息时司机已接单，继续下一步

# 5d. Agent 每 10s 轮询司机位置（司机接单后立即开始，直到行程结束）
python scripts/lobster_cli.py driver-location --order-id "2j08KLO61gHGsc"

# 6. 行程结束后查看详情
python scripts/lobster_cli.py order-detail --order-no "RC20260324405660"

# (可选) 取消订单
python scripts/lobster_cli.py cancel-order --order-id "2j08KLO61gHGsc"
```

## Output Formats

- Default: 人类可读格式
- JSON: 添加 `--json` 参数

```bash
python scripts/lobster_cli.py estimate ... --json
```

## 订单状态说明（重要）

### 订单生命周期中的状态

在整个打车流程中，订单会经历以下状态，**Agent 必须理解这些状态的含义**：

| 状态                 | 阶段     | 含义                          | 是否需要继续轮询                |
| ------------------ | ------ | --------------------------- | ----------------------- |
| **待支付**            | 支付前    | 等待用户支付                      | 是                       |
| **支付成功**           | 支付后    | 用户已完成支付，后台自动创建了打车订单         | 否（继续查询订单状态）             |
| **呼叫中 / 全网呼叫中**    | 司机匹配中  | 订单已创建，正在全网呼叫司机，等待司机接单       | 是                       |
| **司机已接单**          | 司机匹配成功 | 司机已接单，正在赶往上车点               | 否（开始轮询司机位置）             |
| **履约中 / 行程进行中**    | 行程中    | ⭐️ **订单正在执行中**，司机已接单且行程仍在进行 | 是（继续轮询 driver-location） |
| **行程已完成 / 已到达目的地** | 行程结束   | ⭐️ **订单真正完成**，行程已结束         | 否（停止轮询）                 |

### 关键理解

**Agent 必须明确区分这两种状态：**

1. **"支付成功" ≠ 任务结束/打车成功**
   - "支付成功" 仅代表支付流水完成，此时后台才开始真正创建打车单并派单。
   - **Agent 必须** 在收到支付成功反馈后，立即自动执行 `query-order` 和 `driver-location`。
   - **严禁** 在此时向用户发送“打车完成”或“旅途愉快”等结束语并停止轮询。
2. **"履约中"状态 ≠ 订单已完成**
   - "履约中"表示司机正在行驶（接人或送人中）。
   - 此时必须**持续**每 10s 调用 `driver-location` 获取最新位置。
3. **只有"行程已完成"或"已到达目的地"才是真正的任务终点**
   - 只有当 `driver-location` 返回的内容明确包含以下语义时，才停止轮询并结束任务：
     - "行程已完成"
     - "已到达目的地"
     - "行程结束"
     - "感谢使用"

### 例子

**❌ 错误理解（支付完成即退出）：**

```text
Agent 收到 pay-status: "支付成功，正在为您匹配司机"
Agent 对用户说: "支付成功，车一会儿就到，再见！" (然后停止了轮询)
结果: 用户完全不知道车辆动态，流程断裂。
```

**✅ 正确理解（全链路自动执行）：**

```text
1. Agent 确认支付成功
2. Agent 自动调用 query-order 并在司机接单后告知用户车辆信息
3. Agent 自动进入 driver-location 轮询，每 10s 播报位置
4. 直到 driver-location 返回"🏁 您已到达目的地！行程已完成"
5. Agent 对用户说: "您已到达目的地，本次打车服务结束。感谢使用！"
```

## Error Handling

| Error       | Cause         | Solution          |
| ----------- | ------------- | ----------------- |
| `未找到相关地点`   | 搜索无结果         | 换关键词或确认城市名        |
| `API Error` | 服务端返回错误       | 检查参数是否正确          |
| `支付超时`      | 超过 300s 未完成支付 | 手动查询 `pay-status` |
| `MCP Error` | MCP 工具调用失败    | 检查网络和参数           |

## Notes

- `pay` 命令是核心流程：Agent 调用 `pay` 后，必须自动轮询 `pay-status`（每 5s）→ `query-order`（每 5s）→ `driver-location`（每 10s），所有命令都是单次查询立即返回，由 Agent 控制轮询节奏并实时向用户反馈状态
- 坐标格式为字符串 (如 "116.397128")

