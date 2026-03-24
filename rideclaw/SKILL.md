***

name: lobster\_ride
description: A command-line interface tool for ride-hailing service. Provides CLI commands to initialize user profile (home/company address, phone), search locations, estimate prices, pay and create ride orders, query order and driver status, and cancel rides. Use when users need to book a taxi via command line or interact with the Lobster Ride platform.
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
| `pay`             | 生成支付订单 → 等待用户付款 → 支付成功后自动创建打车订单 |
| `pay-status`      | 查询支付状态                          |
| `query-order`     | 查询订单状态和司机信息                     |
| `driver-location` | 获取司机实时位置                        |
| `cancel-order`    | 取消订单                            |
| `order-detail`    | 查询订单详情                          |

## Workflow

1. **初始化**: `python scripts/lobster_cli.py init`
2. **搜索出发地**: `python scripts/lobster_cli.py location-search --keywords "出发地" --city "城市"`
3. **搜索目的地**: `python scripts/lobster_cli.py location-search --keywords "目的地" --city "城市"`
4. **预估价格**: `python scripts/lobster_cli.py estimate --from-lng ... --to-lng ...`
5. **支付并下单**: `python scripts/lobster_cli.py pay --product-category ... --estimate-trace-id ...`
6. **查询订单**: `python scripts/lobster_cli.py query-order --order-id ...`
7. **获取司机位置**: `python scripts/lobster_cli.py driver-location --order-id ...`

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
- `--no-wait`: 只生成订单立即返回，不轮询 (Agent 场景必须加)
- `--phone`: 叫车人手机号 (默认读取 profile)

**Output:**

```
PAY ORDER:
------------------------------------------------------------
  订单号:   RC20260324405660
  金额:     ¥15.00
  支付链接: https://dudubashi.com/rideclaw?order_no=RC20260324405660&mweb_url=...

请打开上方链接完成支付，支付成功后系统将自动为您创建打车订单。
```

拿到输出后，Agent 必须立即将订单号、金额、支付链接发送给用户，然后使用 `pay-status` 查询支付结果。

***

#### pay-status

查询支付状态。支付成功后会自动创建打车订单并返回订单信息。

Agent 在将支付链接发给用户后，应间隔调用此命令查询支付状态，直到支付成功或超时。

```bash
python scripts/lobster_cli.py pay-status --order-no "RC20260324405660"
```

**Parameters:**

- `--order-no, -o`: 支付订单号 (required)

**Output (待支付):**

```
PAY STATUS:
------------------------------------------------------------
  订单号:   RC20260324405660
  支付状态: 待支付
  订单状态: 待支付
```

**Output (已支付):**

```
PAY STATUS:
------------------------------------------------------------
  订单号:   RC20260324405660
  支付状态: 已支付
  订单状态: 已创建
  订单ID:   2j08KLO61gHGsc
```

**Agent 调用流程：**

1. 调用 `pay --no-wait` → 拿到支付链接
2. 立即将支付链接发送给用户
3. 每隔 3 秒调用一次 `pay-status --order-no xxx` 查询
4. 如果返回"已支付"，告知用户订单已创建并返回订单 ID
5. 如果超过 5 分钟仍未支付，提示用户支付超时

#### query-order

查询订单状态和司机信息。

```bash
python scripts/lobster_cli.py query-order \
  --order-id "2j08KLO61gHGsc"
```

#### driver-location

获取司机实时位置。

```bash
python scripts/lobster_cli.py driver-location \
  --order-id "2j08KLO61gHGsc"
```

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

# 5. 支付并自动创建订单（核心步骤）
python scripts/lobster_cli.py pay \
  --estimate-trace-id "0a88bed669c260c39a8704fa9b41b1b0" \
  --from-lng "116.404" --from-lat "39.877" --from-name "永定门桥" \
  --to-lng "116.655" --to-lat "39.854" --to-name "文景东街" \
  --product-category "201" --product-name "特惠快车" --estimate-price 1000
# → 输出支付链接 → 打开链接付款 → 自动轮询 → 支付成功后创建订单
# 记录 order_id

# 6. 查询订单状态（司机接单后可看到司机信息）
python scripts/lobster_cli.py query-order --order-id "2j08KLO61gHGsc"

# 7. 获取司机实时位置
python scripts/lobster_cli.py driver-location --order-id "2j08KLO61gHGsc"

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
- `pay` 命令是核心流程：先付款、后创建订单
- 坐标格式为字符串 (如 "116.397128")
- 支付链接需在浏览器中打开完成微信支付

