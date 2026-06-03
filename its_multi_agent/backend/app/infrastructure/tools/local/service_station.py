import asyncio
import json
import stun
from agents import function_tool
from infrastructure.tools.mcp.mcp_servers import gaode_map_mcp
from infrastructure.logging.logger import logger


def get_ip_via_stun():
    """
        [辅助函数] 获取本机公网 IP
        注意：在服务器部署时，这获取的是服务器机房 IP。
        如果要获取终端用户 IP，建议使用 ContextVars 从 HTTP Header 中透传。
        真正开发期间--->前端请求的时候携带过来---->FastAPI的request携带过来---注入到工具中，工具使用。
    """

    try:
        # 默认使用公用的 STUN 服务器
        nat_type, external_ip, external_port = stun.get_ip_info()
        return external_ip
    except Exception as e:
        print(f"STUN 获取失败: {e}")
        return None
#  从昌平区温都水城到海淀区清华大学（起点明确）--->地址解析得到经纬度
#  我准备去清华大学（起点模糊问题）---->ip找经纬度
#  离我最近的服务站有哪些----？流程:1.先调用resolve_user_location_from_text工具（用户当前的经纬度）---->2.query_nearest_repair_shops_by_coords(用户当前的经纬度)---->最近的服务返回出来

@function_tool
async def resolve_user_location_from_text(
        user_input: str,
) -> str:
    """
    智能解析用户当前位置（起点），用于导航或服务站查询。
    ⚠️ 注意：
    - 仅用于获取**起点**，不可作为终点使用。

    Args:
        user_input (str): 用户提到的**明确地名**。⚠️重要：如果用户只说了"附近"、"这里"、"我的位置"等相对方位词，请**留空**此参数（传空字符串），不要填入这些词。

    返回 JSON 字符串：
    成功时：{"ok": True,  "lat": float, "lng": float, "source": "geocode" | "ip"}
    失败时：{"ok": False, "lat": float, "lng": float, "source": "fallback", "error": str}
    """

    # 1. 相对位置词黑名单 ---
    # LLM 有时会提取出 "附近" 作为参数，但这会导致 Geocode 返回无意义坐标（如城市中心）。
    # 定义这个黑名单，强制这些词触发 IP 定位逻辑。
    RELATIVE_LOCATIONS = {
        "附近", "这", "这里", "这儿", "周围", "周边",
        "我的位置", "当前位置", "所在位置", "nearby", "here"
    }

    user_input = user_input.strip() if user_input else ""

    # 2. 如果输入的是相对词，视为无效输入，清空它以便触发后续 IP 逻辑
    if user_input in RELATIVE_LOCATIONS:
        logger.info(f"[Location] Detected relative term '{user_input}', forcing IP location fallback.")
        user_input = ""

    # 3.  尝试 Geocode（明确地名解）
    if user_input:
        try:
            logger.debug(f"[Location] Trying geocode for: '{user_input}'")

            # 3.1 调用高德地图 MCP 地理编码
            geo_result = await gaode_map_mcp.call_tool(
                tool_name="maps_geo",
                arguments={"address": user_input}
            )

            # 3.2 解析高德 MCP 返回
            # 高德 maps_geo 返回格式：
            # {
            #   "results": [{
            #     "country": "中国",
            #     "province": "浙江省",
            #     "city": "杭州市",
            #     "location": "120.245754,30.227926",   // "lng,lat" 字符串
            #     "level": "住宅区"
            #   }]
            # }
            text = geo_result.content[0].text
            data = json.loads(text)
            results = data.get("results", [])

            if not results:
                logger.warning(f"[Location] Geocode returned empty results for: '{user_input}'")
            else:
                first = results[0]
                location_str = first.get("location", "")
                if location_str and "," in location_str:
                    lng_str, lat_str = location_str.split(",")
                    lat = float(lat_str.strip())
                    lng = float(lng_str.strip())

                    if lat and lng:
                        logger.info(
                            f"[Location] Geocode success: '{user_input}' → ({lat}, {lng}), "
                            f"level={first.get('level', '')}"
                        )
                        return json.dumps({
                            "ok": True,
                            "lat": lat,
                            "lng": lng,
                            "source": "geocode"
                        }, ensure_ascii=False)

                logger.warning(f"[Location] Geocode returned invalid result: {geo_result}")
        except Exception as e:
            # 3.4 如果 Geocode 报错，不抛出异常，而是吞掉错误继续向下走 IP 逻辑
            logger.warning(f"[Location] Geocode failed for '{user_input}': {e}")

    #  获取 IP (注意：此处目前是获取运行环境对外的公网IP，生产环境建议改为前端获取传参注入)
    user_ip = get_ip_via_stun()

    # 4. 尝试 IP 定位
    if user_ip and user_ip not in ("127.0.0.1", "localhost", "::1"):
        try:
            logger.debug(f"[Location] Trying IP location for: {user_ip}")

            # 4.1 调用高德地图 MCP：IP 定位
            ip_result = await gaode_map_mcp.call_tool(
                tool_name="maps_ip_location",
                arguments={"ip": user_ip}
            )

            # 4.2 解析 MCP 返回的 TextContent
            text = ip_result.content[0].text
            data = json.loads(text)

            rectangle = data.get("rectangle", "")
            if not rectangle or ";" not in rectangle:
                logger.warning(f"[Location] IP location returned invalid rectangle: {data}")
                raise ValueError("IP location returned invalid rectangle")

            # 解析边界框，取中心点作为用户经纬度
            bottom_left, top_right = rectangle.split(";")
            bl_lng_str, bl_lat_str = bottom_left.split(",")
            tr_lng_str, tr_lat_str = top_right.split(",")

            bl_lng, bl_lat = float(bl_lng_str.strip()), float(bl_lat_str.strip())
            tr_lng, tr_lat = float(tr_lng_str.strip()), float(tr_lat_str.strip())

            lng = (bl_lng + tr_lng) / 2
            lat = (bl_lat + tr_lat) / 2

            logger.info(
                f"[Location] IP location success: {user_ip} → ({lat:.6f}, {lng:.6f})"
            )
            return json.dumps({
                "ok": True,
                "lat": lat,
                "lng": lng,
                "source": "ip"
            }, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"[Location] IP location failed for {user_ip}: {e}")

    #  5. 兜底
    # 防止整个流程失败导致 Agent 崩溃，返回一个默认坐标（通常是北京天安门）
    fallback_lat, fallback_lng = 39.9042, 116.4074
    logger.info("[Location] Using fallback coordinates (Beijing)")

    return json.dumps({
        "ok": False,
        "error": "无法解析用户位置，使用默认坐标",
        "lat": fallback_lat,
        "lng": fallback_lng,
        "source": "fallback"
    }, ensure_ascii=False)


@function_tool
async def query_nearest_repair_shops_by_coords(
        lat: float,
        lng: float,
        keyword: str = "维修站",
        radius: int = 5000,
        limit: int = 3,
) -> str:
    """
    根据坐标，通过高德地图查询最近的维修站。

    流程：
        1. maps_around_search  周边搜索（结果已按距离排序）
        2. maps_search_detail  获取各 POI 的详细信息

    Args:
        lat (float):   用户纬度 (GCJ-02)
        lng (float):   用户经度 (GCJ-02)
        keyword (str): 搜索关键词，默认 "维修站"
        radius (int):  搜索半径（米），默认 5000
        limit (int):   返回数量上限，默认 3

    Returns:
        str: JSON 字符串，包含距离最近的维修站信息列表。
    """
    location_str = f"{lng},{lat}"

    # -------- 1. 周边搜索（已按距离排序）--------
    try:
        around_result = await gaode_map_mcp.call_tool(
            tool_name="maps_around_search",
            arguments={
                "keywords": keyword,
                "location": location_str,
                "radius": str(radius),
            }
        )
        around_text = around_result.content[0].text
        around_data = json.loads(around_text)
    except Exception as e:
        logger.error(f"[NearestShops] Around search failed: {e}")
        return json.dumps({"ok": False, "error": f"周边搜索失败: {e}"}, ensure_ascii=False)

    # 高德 maps_around_search 返回格式：{"pois": [...]}
    pois = around_data.get("pois", [])
    if not pois:
        logger.info(f"[NearestShops] No POIs found for keyword='{keyword}' near ({lat}, {lng})")
        return json.dumps({
            "ok": True,
            "count": 0,
            "data": [],
            "query": {"lat": lat, "lng": lng, "keyword": keyword, "radius": radius}
        }, ensure_ascii=False)

    # -------- 2. 批量查询 POI 详情 --------
    items = []
    for poi in pois[:limit]:
        detail_data = await _call_maps_search_detail(poi.get("id", ""))
        items.append({
            "id": poi.get("id", ""),
            "name": poi.get("name", ""),
            "typecode": poi.get("typecode", ""),
            "address": poi.get("address", ""),
            "location": poi.get("location", ""),
            "tel": poi.get("tel", ""),
            "detail": detail_data,
        })

    logger.info(
        f"[NearestShops] Returned {len(items)} shops for keyword='{keyword}' "
        f"near ({lat}, {lng}), radius={radius}m"
    )

    return json.dumps({
        "ok": True,
        "count": len(items),
        "data": items,
        "query": {"lat": lat, "lng": lng, "keyword": keyword, "radius": radius, "limit": limit}
    }, ensure_ascii=False, default=str)


async def _call_maps_search_detail(poi_id: str) -> dict:
    """调用 maps_search_detail，返回详细信息字典"""
    try:
        result = await gaode_map_mcp.call_tool(
            tool_name="maps_search_detail",
            arguments={"id": poi_id}
        )
        data = json.loads(result.content[0].text)
        # maps_search_detail 返回单个 POI 对象，无 results 包装
        if not data or "id" not in data:
            return {}
        return {
            "location": data.get("location", ""),
            "city": data.get("city", ""),
            "type": data.get("type", ""),
            "rating": data.get("rating", ""),
            "cost": data.get("cost", ""),
            "opening_hours": data.get("open_time", ""),
            "opentime2": data.get("opentime2", ""),
            "photo": data.get("photo", ""),
            "tel": data.get("tel", ""),
        }
    except Exception as e:
        logger.warning(f"[NearestShops] Detail query failed for POI {poi_id}: {e}")
    return {}


