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

## Quick Start

```bash
# 1. 初始化用户配置（首次使用）
python scripts/lobster_cli.py init

# 2. 搜索地点
python scripts/lobster_cli.py location-search --keywords "北京西站" --city "北京"
```

## Installation

```bash
# Install dependency
pip install httpx
```

## Configuration

- 必须：手机号
- 可选：家，公司

## Available Commands

| Command           | Description                       |
| ----------------- | --------------------------------- |
| `init`            | 初始化用户配置（手机号、城市、家、公司），自动解析地址为坐标    |
| `profile`         | 查看当前用户配置                          |
| `location-search` | 搜索地点                              |
| `place-around`    | 周边 POI 搜索                         |
| `estimate`        | 预估价格和车型                           |
| `pay`             | 生成支付订单 → 等待用户付款 → 支付成功后后台自动创建打车订单 |
| `pay-status`      | 查询支付状态                            |
| `query-order`     | 查询订单状态（含订单状态、司机信息等）               |
| `driver-location` | 获取司机实时位置与行程动态                     |
| `cancel-order`    | 取消订单                              |
| `order-detail`    | 查询订单详情                            |

## Workflow

1. **初始化**: `python scripts/lobster_cli.py init`
2. **搜索出发地**: `python scripts/lobster_cli.py location-search --keywords "出发地" --city "城市"`
3. **搜索目的地**: `python scripts/lobster_cli.py location-search --keywords "目的地" --city "城市"`
4. **确认上下车点（需要用户确认）**: Agent 将搜索到的出发地和目的地整理后展示给用户，等待用户确认无误后再继续。若用户要求修改，重新搜索对应地点。示例：
   ```text
   请确认您的行程信息：
     上车点: 北京西站 - 北京市丰台区莲花池东路118号 (116.322,39.894)
     下车点: 文景东街 - 北京市通州区文景东街 (116.655,39.854)
   确认无误请回复"确认"，如需修改请告诉我。
   ```
5. **预估价格**: 用户确认后，调用 `python scripts/lobster_cli.py estimate --from-lng ... --to-lng ...`
6. **支付下单（自动链式执行，不可拆分）**:
   - 6a. 调用 `pay --no-wait` → 拿到支付链接和订单号 → 立即展示给用户
   - 6b. **紧接着自动调用** `pay-status --order-no xxx` 等待支付结果（无需等待用户回复）
   - 6c. 支付成功后，**紧接着自动调用** `query-order --order-no xxx` 等待司机接单
   - 6d. 司机接单后，**紧接着自动开始**每隔 10s 调用 `driver-location --order-id xxx`，将行程动态告知用户，直到行程结束

> **重要：步骤 4 必须等待用户确认后才能继续。步骤 6a → 6b → 6c → 6d 是一个连续自动执行的链路，Agent 必须在每步命令返回后立即执行下一步，全程不需要用户确认或输入。**

## Command Reference

### Setup Commands

#### init

初始化用户配置。首次使用时运行，绑定手机号和常用地址。地址会自动解析为经纬度。

```bash
python scripts/lobster_cli.py init
```

可通过参数跳过交互式输入:

```bash
python scripts/lobster_cli.py init \
  --phone "13800138000" \
  --city "北京" \
  --home "朝阳区望京SOHO" \
  --company "海淀区中关村软件园"
```

**Output:**

```text
✅ 信息已同步，请确认：
  联系电话:       13800138000
  所在城市:       北京
  常用地址（家）:   朝阳区望京SOHO (望京SOHO 116.481,39.997)
  常用地址（公司）: 海淀区中关村软件园 (中关村软件园 116.303,40.052)

现在可以开始打车了！直接告诉我出发地和目的地即可。
```

#### profile

查看当前用户配置。

```bash
python scripts/lobster_cli.py profile
```

**Output:**

```text
✅ 当前用车信息：
  联系电话:       13800138000
  所在城市:       北京
  常用地址（家）:   朝阳区望京SOHO (望京SOHO 116.481,39.997)
  常用地址（公司）: 海淀区中关村软件园 (中关村软件园 116.303,40.052)

如需修改，可随时重新运行 init。
```

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
🔍 请确认您的具体位置
匹配到多个相似地点，请选择最准确的一个：

1. 北京西站 - 北京市丰台区莲花池东路118号 (116.322,39.894)
2. 北京西站南广场 - 北京市丰台区莲花池东路 (116.321,39.893)
3. 北京西站北广场 - 北京市丰台区北蜂窝路 (116.323,39.897)

请确认序号，或输入更详细的地址重新搜索。
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

生成支付订单并立即返回支付链接。**Agent 拿到输出后必须立即展示支付链接，然后自动调用 `pay-status` 轮询支付状态，整个过程无需等待用户回复。**

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
- `--no-wait`: 只生成订单立即返回，不轮询

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
2. **紧接着自动调用** `pay-status --order-no xxx` 等待支付结果
3. 支付成功后，**紧接着自动调用** `query-order --order-no xxx` 等待司机接单

***

#### pay-status

阻塞式查询支付状态（由 Agent 在 `pay` 返回后自动调用，无需用户触发）。命令会先返回当前状态，然后内部自动轮询直到支付成功或超时。支付成功后会自动创建打车订单。

```bash
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
```

**Parameters:**

- `--order-no, -o`: 支付订单号 (required)
- `--interval`: 轮询间隔秒数 (default: 5)
- `--timeout`: 支付超时秒数 (default: 300)

**Output (支付成功):**

```text
🚗 正在为您呼叫车辆
已成功支付并下发订单，正在为您匹配最优司机。

  路线: 永定门桥 ➜ 文景东街
  已支付: ¥15.00
  状态: 正在全网呼叫中...

提示：匹配成功后我会立即通知您。如需取消，请回复"取消呼叫"。
```

**Agent 调用流程（全程自动执行，不等待用户输入）：**

1. 调用 `pay --no-wait` → 拿到支付链接、订单号、金额
2. **立即**将支付链接展示给用户
3. **紧接着自动调用** `pay-status --order-no xxx` 等待支付结果
4. 支付成功后，**紧接着自动调用** `query-order --order-no xxx` 等待司机接单
5. 司机接单后，**紧接着自动开始**每隔 10s 调用 `driver-location --order-id xxx`，直到行程结束

#### query-order

等待司机接单。命令会先输出"正在为您匹配最佳司机"，然后内部自动轮询直到有司机接单或超时。匹配成功后输出司机信息并返回。

Agent 在 `pay-status` 确认支付成功后，调用此命令等待司机接单即可，无需自行循环调用。

```bash
python scripts/lobster_cli.py query-order \
  --order-no "RC20260324405660"
```

**Parameters:**

- `--order-no, -o`: 订单号 (required)
- `--interval`: 轮询间隔秒数 (default: 5)
- `--timeout`: 匹配超时秒数 (default: 300)

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

获取司机实时位置与行程动态，返回司机当前位置和行程进度信息（如距离终点还有多远等）。行程结束时会返回包含"行程已完成"语义的文本，据此判断是否停止轮询。

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

**Agent 调用流程（全程自动执行，司机接单后立即开始）：**

1. `query-order` 返回司机接单后，**立即自动开始**每隔 10s 调用 `driver-location --order-id xxx`
2. 每次将行程动态告知用户
3. 当 `driver-location` 返回的内容包含行程已完成的语义时，停止轮询，告知用户行程结束

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

# 5. 支付（Agent 自动链式执行 5a→5b→5c，不等待用户输入）
# 5a. 生成支付链接
python scripts/lobster_cli.py pay \
  --estimate-trace-id "0a88bed669c260c39a8704fa9b41b1b0" \
  --from-lng "116.404" --from-lat "39.877" --from-name "永定门桥" \
  --to-lng "116.655" --to-lat "39.854" --to-name "文景东街" \
  --product-category "201" --product-name "特惠快车" --estimate-price 1000 \
  --no-wait
# → 立即展示支付链接给用户

# 5b. 自动轮询支付状态（无需用户确认，紧接着执行）
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
# → 支付成功后后台自动创建打车订单

# 5c. 自动等待司机接单（支付成功后紧接着执行）
python scripts/lobster_cli.py query-order --order-no "RC20260324405660"

# 5d. 司机接单后自动轮询司机位置（每10s，直到行程结束）
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

## Error Handling

| Error       | Cause         | Solution          |
| ----------- | ------------- | ----------------- |
| `未找到相关地点`   | 搜索无结果         | 换关键词或确认城市名        |
| `API Error` | 服务端返回错误       | 检查参数是否正确          |
| `支付超时`      | 超过 300s 未完成支付 | 手动查询 `pay-status` |
| `MCP Error` | MCP 工具调用失败    | 检查网络和参数           |

## Notes

- 首次使用请先运行 `init` 绑定手机号
- `pay` 命令是核心流程：Agent 调用 `pay --no-wait` 后，必须自动链式执行 `pay-status` → `query-order` → `driver-location` 轮询，全程不需要用户确认
- 坐标格式为字符串 (如 "116.397128")

