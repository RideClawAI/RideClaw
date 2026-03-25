````Markdown
***

name: lobster\_ride
description: A command-line interface tool for ride-hailing service. Provides CLI commands to initialize user profile (home/company address, phone), search locations, estimate prices, pay and create ride orders, query order and driver status, and cancel rides. Use when users need to book a taxi via command line or interact with the Lobster Ride platform.

***

# 龙虾出行 CLI

龙虾出行命令行打车工具，支持全流程打车服务。

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

| Command           | Description                     |
| ----------------- | ------------------------------- |
| `init`            | 初始化用户配置（手机号、城市、家、公司），自动解析地址为坐标  |
| `profile`         | 查看当前用户配置                        |
| `location-search` | 搜索地点                            |
| `place-around`    | 周边 POI 搜索                       |
| `estimate`        | 预估价格和车型                         |
| `pay`             | 生成支付订单 → 等待用户付款 → 支付成功后后台自动创建打车订单 |
| `pay-status`      | 查询支付状态                          |
| `query-order`     | 查询订单状态（含订单状态、司机信息等）           |
| `driver-location` | 获取司机实时位置与行程动态                   |
| `cancel-order`    | 取消订单                            |
| `order-detail`    | 查询订单详情                          |

## Workflow

1. **初始化**: `python scripts/lobster_cli.py init`
2. **搜索出发地**: `python scripts/lobster_cli.py location-search --keywords "出发地" --city "城市"`
3. **搜索目的地**: `python scripts/lobster_cli.py location-search --keywords "目的地" --city "城市"`
4. **预估价格**: `python scripts/lobster_cli.py estimate --from-lng ... --to-lng ...`
5. **支付并下单**: `python scripts/lobster_cli.py pay --product-category ... --estimate-trace-id ...`
6. **查询订单**: `python scripts/lobster_cli.py query-order --order-no ...`
7. **获取司机位置**: `python scripts/lobster_cli.py driver-location --order-id ...`

## Command Reference

### Setup Commands

#### init

初始化用户配置。首次使用时运行，绑定手机号和常用地址。地址会自动解析为经纬度。

**Agent 回复示例（首次使用引导流程）：**

> **安装完成后：**
> 已安装rideclaw skill，这个skill可以为您便捷打车。
>
> - 自然语言交互：支持"打车去公司"、"帮我叫辆便宜的车"等口语化指令
> - 多平台呼叫：聚合主流打车平台，一键全网呼叫
> - 智能估价与预估：实时同步各车型价格、行驶里程及预计到达时间
> - 常用地址记忆：支持预设"家/公司"地址，实现秒级发单
>
> 为了确保正常叫车，请先告诉我用车人手机号：

> **手机号设置完成后：**
> 手机号已收到，你也可以设置常用地址
> 比如：家在哪里与公司在哪里
> 如果不设置，也可以直接开始打车

> **全部信息填入后：**
> ✅ 信息已同步，请确认：
> 联系电话： 138****8888
> 常用地址（家）： 朝阳区望京SOHO
> 常用地址（公司）： 海淀区中关村软件园

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

#### profile

查看当前用户配置。

```bash
python scripts/lobster_cli.py profile
```

**Output:**

```
USER PROFILE:
----------------------------------------
  手机号:   13800138000
  城市:     北京
  家:       朝阳区望京SOHO
            (望京SOHO  116.481,39.997)
  公司:     海淀区中关村软件园
            (中关村软件园  116.303,40.052)
```

### Location Commands

#### location-search

搜索地点，获取名称和坐标。

**Agent 回复示例（地点确认）：**

> 🔍 请确认您的具体位置
> 匹配到多个相似地点，请选择最准确的一个：
>
> 出发地：
> 1. 北京西站 - 北京市丰台区莲花池东路118号 (116.322,39.894)
> 2. 北京西站南广场 - 北京市丰台区莲花池东路 (116.321,39.891)
>
> 目的地：
> 1. 东方科技大厦 - 北京市海淀区中关村南大街 (116.326,39.955)
> 2. 东方科技大厦A座 - 北京市海淀区中关村南大街2号 (116.325,39.954)
>
> 请确认，或输入更详细的地址重新搜索。

```bash
python scripts/lobster_cli.py location-search \
  --keywords "北京西站" \
  --city "北京"
```

**Parameters:**

- `--keywords, -k`: 搜索关键词 (required)
- `--city, -c`: 城市名称 (required)

**Output:**

```
LOCATIONS:
------------------------------------------------------------
1. 北京西站
   地址: 北京市丰台区莲花池东路118号
   坐标: 116.322,39.894
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

**Agent 回复示例（规划行程+推荐车型）：**

> 您的上车点是 永定门桥，为您规划前往 文景东街 的用车行程。我将通过龙虾出行为您提供服务。
> 车型推荐： 经济/特惠快车
> 预估价格： ¥10.00 ~ ¥15.00
> 预估时间： 预计行驶19分钟
> 如果需要调整起终点，随时和我说。如果确认叫车，我将为您生成支付链接。

> **用户要求查看更多车型时：**
> 已为您搜索到多种车型
> 从 永定门桥 前往 文景东街，各车型实时价格如下：
> 车型 &emsp; 预估价格
> 特惠快车 &emsp; ¥10.00
> 快车 &emsp; ¥15.00
> 专车 &emsp; ¥30.00
> 豪华车 &emsp; ¥100.00
> 您想选哪个？请直接回复车型名称（如："选特惠快车"）。

```bash
python scripts/lobster_cli.py estimate \
  --from-lng "116.404" \
  --from-lat "39.877" \
  --from-name "永定门桥" \
  --to-lng "116.655" \
  --to-lat "39.854" \
  --to-name "文景东街"
```

**Output:**

```
PRICE ESTIMATE:
------------------------------------------------------------
  特惠快车
    价格: ¥10.00
    品类代码: 201

  快车
    价格: ¥15.00
    品类代码: 1

  专车
    价格: ¥30.00
    品类代码: 8

  豪华车
    价格: ¥100.00
    品类代码: 17

预估流程ID: 0a88bed669c260c39a8704fa9b41b1b0
```

#### pay

生成支付订单并立即返回支付链接。Agent 必须先将支付链接发送给用户，然后再通过 `pay-status` 轮询支付状态。

**Agent 回复示例（生成支付链接后立即发给用户）：**

> 您的上车点是 永定门桥，为您规划前往 文景东街 的用车行程。我将通过龙虾出行为您提供服务。
> 车型推荐： 经济/特惠快车
> 预估价格： ¥15.00
> 预估时间： 预计行驶19分钟
> 支付链接: https://dudubashi.com/rideclaw?order_no=RC20260324405660&mweb_url=...
> 如果需要调整起终点或者用车偏好，随时和我说。如果现在叫车，请点击链接支付后和我说

> **重要**：必须使用 `--no-wait` 参数，确保命令立即返回支付链接，不要在命令内部轮询。

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

```
PAY ORDER:
------------------------------------------------------------
  订单号:   RC20260324405660
  金额:     ¥15.00
  支付链接: https://dudubashi.com/rideclaw?order_no=RC20260324405660&mweb_url=...

请打开上方链接完成支付，支付成功后系统将自动为您创建打车订单。
```

拿到输出后，Agent 必须立即将订单号、金额、支付链接发送给用户，然后使用 `pay-status` 等待支付结果。

---

#### pay-status

阻塞式查询支付状态。命令会先返回当前状态，然后内部自动轮询直到支付成功或超时。支付成功后会自动创建打车订单。

Agent 在将支付链接发给用户后，调用此命令等待支付结果即可，无需自行循环调用。

```bash
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
```

**Parameters:**

- `--order-no, -o`: 支付订单号 (required)
- `--interval`: 轮询间隔秒数 (default: 5)
- `--timeout`: 支付超时秒数 (default: 300)

**Output (支付成功):**

```
PAY STATUS:
------------------------------------------------------------
  订单号:   RC20260324405660
  支付状态: 待支付
  订单状态: 待支付

等待支付中 (每 5s 查询，超时 300s) ...
PAY STATUS:
------------------------------------------------------------
  订单号:   RC20260324405660
  支付状态: 已支付
  订单状态: 已创建

支付成功！后台已自动为您创建打车订单。
```

**Agent 调用流程：**

1. 调用 `pay` → 拿到支付链接、订单号、金额
2. **立即**将支付链接发送给用户
3. 调用 `pay-status --order-no xxx`，命令会阻塞等待支付结果
4. 命令返回后，将支付结果告知用户（成功/超时）

#### query-order

阻塞式等待司机接单。命令会先输出"正在为您匹配最佳司机"，然后内部自动轮询直到有司机接单或超时。匹配成功后输出司机信息并返回。

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

```
ORDER STATUS:
------------------------------------------------------------
  正在为您匹配最佳司机，请耐心等待...

等待司机接单中 (每 5s 查询，超时 300s) ...
ORDER STATUS:
------------------------------------------------------------
  已为您匹配到最佳司机！
  司机: 张师傅
  电话: 138****1234
  车辆: 丰田卡罗拉 (京A·12345)
```

---

#### driver-location

获取司机实时位置与行程动态，返回司机当前位置和行程进度信息（如距离终点还有多远等）。行程结束时会返回包含"行程已完成"语义的文本，Agent 据此判断是否停止轮询。

```bash
python scripts/lobster_cli.py driver-location \
  --order-id "2j08KLO61gHGsc"
```

**Parameters:**

- `--order-id, -o`: 订单 ID (required)

**Output (行程中):**

```
TRIP STATUS & DRIVER LOCATION:
------------------------------------------------------------
  司机张师傅正在赶来接您
  当前距离您还有2.3公里，预计3分钟到达
  车辆信息：丰田卡罗拉 京A·12345
```

**Output (行程结束):**

```
TRIP STATUS & DRIVER LOCATION:
------------------------------------------------------------
  ✅ 行程已完成！
  👨‍💼 司机信息：
  • 称呼：张师傅
  • 车型：丰田卡罗拉
  • 车牌：京A·12345
  🌟 感谢您的使用，如果满意请给司机好评！
```

**Agent 调用流程：**

1. `pay-status` 返回支付成功后，调用 `query-order --order-no xxx`，命令会阻塞等待司机接单
2. 命令返回后，将司机信息告知用户
3. 然后每隔 10s 调用 `driver-location --order-id xxx`，将行程动态返回给用户
4. 当 `driver-location` 返回的内容包含行程已完成的语义时，停止轮询，告知用户行程结束

#### cancel-order

取消订单。

```bash
python scripts/lobster_cli.py cancel-order \
  --order-id "2j08KLO61gHGsc"
```

#### order-detail

查询订单完整详情（含最终费用、司机信息等）。

```bash
python scripts/lobster_cli.py order-detail \
  --order-no "RC20260324405660"
```

**Output:**

```
ORDER DETAIL:
------------------------------------------------------------
  订单号:   RC20260324405660
  创建时间: 2026-03-24 18:05:35
  状态:     已完成
  支付状态: 已支付
  出发地:   永定门桥
  目的地:   文景东街
  车型:     快车
  预估价格: ¥15.00
  实际价格: ¥14.50
  司机:     张师傅
  车牌:     京A·12345
  电话:     138****1234
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

# 5. 支付（核心步骤，支付成功后后台自动创建订单）
python scripts/lobster_cli.py pay \
  --estimate-trace-id "0a88bed669c260c39a8704fa9b41b1b0" \
  --from-lng "116.404" --from-lat "39.877" --from-name "永定门桥" \
  --to-lng "116.655" --to-lat "39.854" --to-name "文景东街" \
  --product-category "201" --product-name "特惠快车" --estimate-price 1000
# → 输出支付链接 → 打开链接付款 → 自动轮询 → 支付成功后后台自动创建订单
# 记录 order_id

# 6. 等待司机接单（阻塞轮询，匹配成功后返回司机信息）
python scripts/lobster_cli.py query-order --order-no "RC20260324405660"

# 7. 获取司机实时位置（每10s调用一次，直到行程结束）
python scripts/lobster_cli.py driver-location --order-id "2j08KLO61gHGsc"
# Agent 根据返回内容判断行程是否结束，结束则停止轮询

# 8. 行程结束后查看详情
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
- `pay` 命令是核心流程：用户付款成功后，后台自动创建打车订单，Agent 不需要再调用创建订单接口
- 坐标格式为字符串 (如 "116.397128")

````

