#!/usr/bin/env python3
"""
龙虾出行 CLI - 命令行打车工具
通过龙虾出行服务完成地点搜索、预估、支付、下单全流程
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

import httpx


# ── 默认配置 ──────────────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "https://rideclaw.dudubashi.com/api/v1/"

CONFIG_DIR = Path.home() / ".lobster_ride"
CONFIG_FILE = CONFIG_DIR / "profile.json"


# ── 用户配置 ──────────────────────────────────────────────────────────────────

def load_profile() -> Dict[str, Any]:
    """加载用户配置"""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(profile: Dict[str, Any]) -> None:
    """保存用户配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def init_profile(phone: Optional[str] = None,
                 home: Optional[str] = None,
                 company: Optional[str] = None,
                 city: Optional[str] = None,
                 client: Optional["LobsterClient"] = None) -> Dict[str, Any]:
    """初始化用户配置，支持命令行传参或交互式输入"""
    profile = load_profile()

    if phone is None:
        phone = input(f"手机号 [{profile.get('phone', '')}]: ").strip()
    if phone:
        profile["phone"] = phone

    if city is None:
        city = input(f"所在城市 [{profile.get('city', '')}]: ").strip()
    if city:
        profile["city"] = city

    if home is None:
        home = input(f"家庭地址 [{profile.get('home', '')}]: ").strip()
    if home:
        profile["home"] = home
        if client and profile.get("city"):
            geo = _geocode_address(client, home, profile["city"])
            if geo:
                profile["home_location"] = geo

    if company is None:
        company = input(f"公司地址 [{profile.get('company', '')}]: ").strip()
    if company:
        profile["company"] = company
        if client and profile.get("city"):
            geo = _geocode_address(client, company, profile["city"])
            if geo:
                profile["company_location"] = geo

    save_profile(profile)
    return profile


def _geocode_address(client: "LobsterClient", address: str, city: str) -> Optional[Dict[str, Any]]:
    """将地址解析为经纬度"""
    try:
        result = client.search_location(address, city)
        text = _parse_mcp_text(result)
        pois = _parse_location_list(text)
        if pois:
            poi = pois[0]
            loc = poi.get("location", {})
            return {
                "name": poi.get("display_name", poi.get("name", address)),
                "lng": str(loc.get("lng", "")),
                "lat": str(loc.get("lat", "")),
            }
    except Exception:
        pass
    return None


def format_profile(profile: Dict[str, Any]) -> str:
    """格式化显示用户配置"""
    if not profile:
        return "尚未初始化，请运行: lobster-cli init"

    lines = ["USER PROFILE:", "-" * 40]
    lines.append(f"  手机号:   {profile.get('phone', '未设置')}")
    lines.append(f"  城市:     {profile.get('city', '未设置')}")
    lines.append(f"  家:       {profile.get('home', '未设置')}")
    if profile.get("home_location"):
        loc = profile["home_location"]
        lines.append(f"            ({loc.get('name', '')}  {loc.get('lng', '')},{loc.get('lat', '')})")
    lines.append(f"  公司:     {profile.get('company', '未设置')}")
    if profile.get("company_location"):
        loc = profile["company_location"]
        lines.append(f"            ({loc.get('name', '')}  {loc.get('lng', '')},{loc.get('lat', '')})")
    return "\n".join(lines)


# ── 客户端 ────────────────────────────────────────────────────────────────────

class LobsterClient:
    """龙虾出行客户端 — MCP (JSON-RPC) + REST 混合调用"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (
            base_url
            or os.environ.get("LOBSTER_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self.client = httpx.Client(timeout=30.0,verify=False)

    # ── MCP JSON-RPC 底层 ──

    def _mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用 MCP 工具 (JSON-RPC 2.0)"""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": 1,
        }
        response = self.client.post(f"{self.base_url}/mcp", json=payload)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise RuntimeError(f"MCP Error: {result['error']}")

        return result.get("result", {})

    # ── REST 底层 ──

    def _rest_post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """REST POST 请求"""
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.client.post(url, json=body)
        response.raise_for_status()
        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API Error: {result.get('message', 'unknown')}")
        return result.get("data", {})

    def _rest_get(self, path: str) -> Dict[str, Any]:
        """REST GET 请求"""
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.client.get(url)
        response.raise_for_status()
        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API Error: {result.get('message', 'unknown')}")
        return result.get("data", {})

    # ── 地图 (MCP) ──

    def search_location(self, keywords: str, city: str) -> Dict[str, Any]:
        """搜索地点"""
        return self._mcp_call("maps_textsearch", {
            "keywords": keywords,
            "city": city,
        })

    def place_around(self, location: str, keyword: str = "",
                     radius: int = 1000) -> Dict[str, Any]:
        """周边 POI 搜索"""
        args: Dict[str, Any] = {"location": location}
        if keyword:
            args["keyword"] = keyword
        if radius != 1000:
            args["radius"] = str(radius)
        return self._mcp_call("maps_place_around", args)

    # ── 预估 (REST) ──

    def estimate_price(
        self,
        from_lng: str, from_lat: str, from_name: str,
        to_lng: str, to_lat: str, to_name: str,
    ) -> Dict[str, Any]:
        """预估价格"""
        return self._rest_post("order/estimate", {
            "from_lng": from_lng,
            "from_lat": from_lat,
            "from_name": from_name,
            "to_lng": to_lng,
            "to_lat": to_lat,
            "to_name": to_name,
        })

    # ── 支付 (REST) ──

    def create_pay_order(
        self,
        estimate_trace_id: str,
        from_lng: str, from_lat: str, from_name: str,
        to_lng: str, to_lat: str, to_name: str,
        product_category: str,
        product_name: str,
        estimate_price: int,
    ) -> Dict[str, Any]:
        """生成支付订单，返回 pay_url"""
        return self._rest_post("order/create", {
            "estimate_trace_id": estimate_trace_id,
            "from_lng": from_lng,
            "from_lat": from_lat,
            "from_name": from_name,
            "to_lng": to_lng,
            "to_lat": to_lat,
            "to_name": to_name,
            "product_category": product_category,
            "product_name": product_name,
            "estimate_price": estimate_price,
        })

    def pay_status(self, order_no: str) -> Dict[str, Any]:
        """查询支付状态"""
        return self._rest_get(f"order/{order_no}/pay-status")

    def order_detail(self, order_no: str) -> Dict[str, Any]:
        """查询订单详情"""
        return self._rest_get(f"order/{order_no}/detail")

    # ── 打车 (MCP) ──

    def create_ride_order(
        self,
        product_category: str,
        estimate_trace_id: str,
        phone: str = "",
    ) -> Dict[str, Any]:
        """创建真实打车订单（支付成功后调用）"""
        return self._mcp_call("taxi_create_order", {
            "product_category": product_category,
            "estimate_trace_id": estimate_trace_id,
            "caller_car_phone": phone,
        })

    def query_order(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态"""
        return self._mcp_call("taxi_query_order", {
            "order_id": order_id,
        })

    def get_driver_location(self, order_id: str) -> Dict[str, Any]:
        """获取司机位置"""
        return self._mcp_call("taxi_get_driver_location", {
            "order_id": order_id,
        })

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """取消订单"""
        return self._mcp_call("taxi_cancel_order", {
            "order_id": order_id,
        })


# ── 输出格式化 ────────────────────────────────────────────────────────────────

def _parse_mcp_text(result: Dict[str, Any]) -> str:
    """从 MCP content 数组中提取 text"""
    content = result.get("content", [])
    if content and isinstance(content, list):
        return content[0].get("text", "")
    return json.dumps(result, indent=2, ensure_ascii=False)


def _parse_location_list(text: str) -> List[Dict[str, Any]]:
    """从 maps_textsearch 返回的 JSON 字符串解析 POI 列表"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []


def format_location_result(result: Dict[str, Any]) -> str:
    """格式化地点搜索结果"""
    text = _parse_mcp_text(result)
    pois = _parse_location_list(text)

    if not pois:
        return text or "未找到相关地点。"

    lines = ["LOCATIONS:", "-" * 60]
    for i, poi in enumerate(pois[:10], 1):
        loc = poi.get("location", {})
        coord = f"{loc.get('lng', 'N/A')},{loc.get('lat', 'N/A')}" if isinstance(loc, dict) else str(loc)
        lines.append(f"{i}. {poi.get('display_name', poi.get('name', 'N/A'))}")
        lines.append(f"   地址: {poi.get('address', 'N/A')}")
        lines.append(f"   坐标: {coord}")
        lines.append("")
    return "\n".join(lines)


def format_estimate_result(data: Dict[str, Any]) -> str:
    """格式化预估价格结果"""
    products = data.get("products", [])
    if not products:
        return json.dumps(data, indent=2, ensure_ascii=False)

    trace_id = data.get("estimate_trace_id", "N/A")
    lines = ["PRICE ESTIMATE:", "-" * 60]
    for p in products:
        price = p.get("estimate_price", 0)
        price_yuan = price / 100 if isinstance(price, (int, float)) else price
        lines.append(f"  {p.get('product_name', 'N/A')}")
        lines.append(f"    价格: ¥{price_yuan:.2f}")
        lines.append(f"    品类代码: {p.get('product_category', 'N/A')}")
        lines.append("")
    lines.append(f"预估流程ID: {trace_id}")
    return "\n".join(lines)


def format_pay_order(data: Dict[str, Any]) -> str:
    """格式化支付订单"""
    amount = data.get("amount", 0)
    amount_yuan = amount / 100 if isinstance(amount, (int, float)) else amount
    lines = ["PAY ORDER:", "-" * 60]
    lines.append(f"  订单号:   {data.get('order_no', 'N/A')}")
    lines.append(f"  金额:     ¥{amount_yuan:.2f}")
    lines.append(f"  支付链接: {data.get('pay_url', 'N/A')}")
    lines.append("")
    lines.append("请打开上方链接完成支付，支付成功后系统将自动为您创建打车订单。")
    return "\n".join(lines)


def format_pay_status(data: Dict[str, Any]) -> str:
    """格式化支付状态"""
    lines = ["PAY STATUS:", "-" * 60]
    lines.append(f"  订单号:   {data.get('order_no', 'N/A')}")
    lines.append(f"  支付状态: {data.get('pay_status_text', 'N/A')}")
    lines.append(f"  订单状态: {data.get('order_status_text', 'N/A')}")
    return "\n".join(lines)


def format_order_result(result: Dict[str, Any]) -> str:
    """格式化 MCP 订单操作结果"""
    return _parse_mcp_text(result)


def format_driver_location(result: Dict[str, Any]) -> str:
    """格式化司机位置"""
    return _parse_mcp_text(result)


def format_order_detail(data: Dict[str, Any]) -> str:
    """格式化订单详情"""
    est_price = data.get("estimate_price")
    est_str = f"¥{est_price / 100:.2f}" if isinstance(est_price, (int, float)) else "N/A"
    actual = data.get("actual_price")
    actual_str = f"¥{actual / 100:.2f}" if isinstance(actual, (int, float)) else "N/A"

    lines = ["ORDER DETAIL:", "-" * 60]
    lines.append(f"  订单号:   {data.get('order_no', 'N/A')}")
    lines.append(f"  创建时间: {data.get('created_at', 'N/A')}")
    lines.append(f"  状态:     {data.get('status_text', 'N/A')}")
    lines.append(f"  支付状态: {data.get('pay_status_text', 'N/A')}")
    lines.append(f"  出发地:   {data.get('from_name', 'N/A')}")
    lines.append(f"  目的地:   {data.get('to_name', 'N/A')}")
    lines.append(f"  车型:     {data.get('product_name', 'N/A')}")
    lines.append(f"  预估价格: {est_str}")
    lines.append(f"  实际价格: {actual_str}")

    driver = data.get("driver")
    if driver:
        lines.append(f"  司机:     {driver.get('name', 'N/A')}")
        lines.append(f"  车牌:     {driver.get('plate', 'N/A')}")
        lines.append(f"  电话:     {driver.get('phone', 'N/A')}")
    else:
        lines.append("  司机:     等待接单")

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="龙虾出行 CLI - 命令行打车工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
环境变量:
  LOBSTER_BASE_URL   API Base URL (可选，默认: http://rideclaw.dudubashi.com/api/v1/)

示例:
  lobster-cli init
  lobster-cli location-search --keywords "北京西站" --city "北京"
  lobster-cli estimate --from-lng 116.404 --from-lat 39.877 --from-name "永定门桥" \\
                       --to-lng 116.655 --to-lat 39.854 --to-name "文景东街"
""",
    )

    parser.add_argument("--base-url", help="API Base URL (也可通过 LOBSTER_BASE_URL 设置)")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    sub = parser.add_subparsers(dest="command", help="可用命令")

    # ── init ──
    init_p = sub.add_parser("init", help="初始化用户配置（手机号、城市、家、公司）")
    init_p.add_argument("--phone", help="手机号")
    init_p.add_argument("--city", help="所在城市")
    init_p.add_argument("--home", help="家庭地址")
    init_p.add_argument("--company", help="公司地址")

    # ── profile ──
    sub.add_parser("profile", help="查看用户配置")

    # ── location-search ──
    loc_p = sub.add_parser("location-search", help="搜索地点")
    loc_p.add_argument("--keywords", "-k", required=True, help="搜索关键词")
    loc_p.add_argument("--city", "-c", required=True, help="城市名称")

    # ── place-around ──
    pa_p = sub.add_parser("place-around", help="周边 POI 搜索")
    pa_p.add_argument("--location", "-l", required=True, help="中心坐标 (lng,lat)")
    pa_p.add_argument("--keyword", "-k", default="", help="搜索关键词")
    pa_p.add_argument("--radius", "-r", type=int, default=1000, help="搜索半径(米)")

    # ── estimate ──
    est_p = sub.add_parser("estimate", help="预估价格")
    est_p.add_argument("--from-lng", required=True, help="出发经度")
    est_p.add_argument("--from-lat", required=True, help="出发纬度")
    est_p.add_argument("--from-name", required=True, help="出发地名称")
    est_p.add_argument("--to-lng", required=True, help="目的经度")
    est_p.add_argument("--to-lat", required=True, help="目的纬度")
    est_p.add_argument("--to-name", required=True, help="目的地名称")

    # ── pay ──
    pay_p = sub.add_parser("pay", help="生成支付订单并等待付款")
    pay_p.add_argument("--estimate-trace-id", "-e", required=True, help="预估流程 ID")
    pay_p.add_argument("--from-lng", required=True, help="出发经度")
    pay_p.add_argument("--from-lat", required=True, help="出发纬度")
    pay_p.add_argument("--from-name", required=True, help="出发地名称")
    pay_p.add_argument("--to-lng", required=True, help="目的经度")
    pay_p.add_argument("--to-lat", required=True, help="目的纬度")
    pay_p.add_argument("--to-name", required=True, help="目的地名称")
    pay_p.add_argument("--product-category", "-p", required=True, help="车型品类代码")
    pay_p.add_argument("--product-name", required=True, help="车型名称")
    pay_p.add_argument("--estimate-price", required=True, type=int, help="预估价格 (分)")
    pay_p.add_argument("--no-wait", action="store_true", default=False,
                       help="只生成支付订单，不轮询等待支付")
    pay_p.add_argument("--interval", type=int, default=3, help="轮询间隔秒数 (默认 3)")
    pay_p.add_argument("--timeout", type=int, default=300, help="支付超时秒数 (默认 300)")
    pay_p.add_argument("--phone", help="叫车人手机号 (默认读取 profile)")

    # ── pay-status ──
    ps_p = sub.add_parser("pay-status", help="查询支付状态")
    ps_p.add_argument("--order-no", "-o", required=True, help="订单号")

    # ── query-order ──
    qo_p = sub.add_parser("query-order", help="查询订单状态")
    qo_p.add_argument("--order-id", "-o", required=True, help="订单 ID")

    # ── driver-location ──
    dl_p = sub.add_parser("driver-location", help="获取司机位置")
    dl_p.add_argument("--order-id", "-o", required=True, help="订单 ID")

    # ── cancel-order ──
    ca_p = sub.add_parser("cancel-order", help="取消订单")
    ca_p.add_argument("--order-id", "-o", required=True, help="订单 ID")

    # ── order-detail ──
    od_p = sub.add_parser("order-detail", help="查询订单详情")
    od_p.add_argument("--order-no", "-o", required=True, help="订单号")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ── 本地命令 ──
    if args.command == "init":
        client = LobsterClient(base_url=args.base_url)
        profile = init_profile(
            phone=args.phone,
            home=args.home,
            company=args.company,
            city=args.city,
            client=client,
        )
        print("配置已保存。\n")
        print(format_profile(profile))
        return

    if args.command == "profile":
        profile = load_profile()
        if args.json:
            print(json.dumps(profile, indent=2, ensure_ascii=False))
        else:
            print(format_profile(profile))
        return

    # ── 网络命令 ──
    try:
        client = LobsterClient(base_url=args.base_url)

        if args.command == "location-search":
            result = client.search_location(args.keywords, args.city)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_location_result(result))

        elif args.command == "place-around":
            result = client.place_around(args.location, args.keyword, args.radius)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_location_result(result))

        elif args.command == "estimate":
            data = client.estimate_price(
                args.from_lng, args.from_lat, args.from_name,
                args.to_lng, args.to_lat, args.to_name,
            )
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(format_estimate_result(data))

        elif args.command == "pay":
            # 步骤 1: 生成支付订单
            data = client.create_pay_order(
                estimate_trace_id=args.estimate_trace_id,
                from_lng=args.from_lng, from_lat=args.from_lat, from_name=args.from_name,
                to_lng=args.to_lng, to_lat=args.to_lat, to_name=args.to_name,
                product_category=args.product_category,
                product_name=args.product_name,
                estimate_price=args.estimate_price,
            )
            order_no = data.get("order_no", "")
            print(format_pay_order(data))

            if args.no_wait or not order_no:
                return

            # 步骤 2: 轮询等待支付
            print(f"\n等待支付中 (每 {args.interval}s 查询一次，超时 {args.timeout}s) ...")
            start = time.time()
            paid = False
            while time.time() - start < args.timeout:
                time.sleep(args.interval)
                status = client.pay_status(order_no)
                pay_st = status.get("pay_status", 0)
                elapsed = int(time.time() - start)
                print(f"  [{elapsed}s] {status.get('pay_status_text', '查询中...')}")
                if pay_st == 2:  # 已支付
                    paid = True
                    break

            if not paid:
                print("\n支付超时，请手动查询: lobster-cli pay-status --order-no " + order_no)
                return

            # 步骤 3: 支付成功 → 创建真实打车订单
            print("\n支付成功！正在为您创建打车订单 ...")
            phone = args.phone or load_profile().get("phone", "")
            ride_result = client.create_ride_order(
                args.product_category, args.estimate_trace_id, phone,
            )
            print(format_order_result(ride_result))

        elif args.command == "pay-status":
            data = client.pay_status(args.order_no)
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(format_pay_status(data))

        elif args.command == "query-order":
            result = client.query_order(args.order_id)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_order_result(result))

        elif args.command == "driver-location":
            result = client.get_driver_location(args.order_id)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_driver_location(result))

        elif args.command == "cancel-order":
            result = client.cancel_order(args.order_id)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_order_result(result))

        elif args.command == "order-detail":
            data = client.order_detail(args.order_no)
            if args.json:
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(format_order_detail(data))

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
