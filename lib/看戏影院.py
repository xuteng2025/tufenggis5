# coding=utf-8
#!/usr/bin/python
"""
看戏影院 - 根据 HTML 页面结构实现
支持：
1) 首页推荐/分类筛选
2) 搜索功能
3) 详情页解析（含播放线路和剧集）
4) 播放地址解析
5) 分页支持
"""
import base64
import hashlib
import json
import re
import sys
import time
from html.parser import HTMLParser

sys.path.append('..')
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    """看戏影院爬虫"""

    # API 配置
    HOST = "https://www.kanxige.com"
    BASE = "/"

    # 分类映射
    CATS = [
        ('1', '电影'),
        ('2', '电视剧'),
        ('3', '综艺'),
        ('4', '动漫'),
        ('5', '排行榜'),
        ('6', '最近更新')
    ]

    # 筛选配置（按分类）
    FILTERS = {
        '1': {
            'cate': {'label': '子类型', 'options': [('', '全部'), ('5', '动作片'), ('6', '喜剧片'),
                ('7', '爱情片'), ('8', '科幻片'), ('9', '恐怖片'), ('10', '剧情片'), ('11', '战争片')]},
            'area': {'label': '地区', 'options': [('', '全部'), ('大陆', '大陆'), ('台湾', '台湾'),
                ('日本', '日本'), ('法国', '法国'), ('印度', '印度'), ('加拿大', '加拿大'),
                ('俄罗斯', '俄罗斯'), ('新加坡', '新加坡'), ('其它', '其它')]},
            'year': {'label': '年份', 'options': [('', '全部'), ('2026', '2026'), ('2025', '2025'),
                ('2024', '2024'), ('2023', '2023'), ('2022', '2022'), ('2021', '2021'),
                ('2020', '2020'), ('2019', '2019'), ('2018', '2018'), ('2017', '2017'),
                ('2016', '2016'), ('2015', '2015'), ('2014', '2014'), ('2013', '2013'),
                ('2012', '2012'), ('2011', '2011'), ('2010', '2010')]}
        },
        '2': {
            'cate': {'label': '子类型', 'options': [('', '全部'), ('12', '国产剧'), ('13', '港台剧'),
                ('14', '日韩剧'), ('15', '欧美剧'), ('16', '海外剧')]},
            'area': {'label': '地区', 'options': [('', '全部'), ('大陆', '大陆'), ('台湾', '台湾'),
                ('日本', '日本'), ('韩国', '韩国'), ('欧美', '欧美'), ('其它', '其它')]},
            'year': {'label': '年份', 'options': [('', '全部'), ('2026', '2026'), ('2025', '2025'),
                ('2024', '2024'), ('2023', '2023'), ('2022', '2022'), ('2021', '2021'),
                ('2020', '2020'), ('2019', '2019'), ('2018', '2018'), ('2017', '2017'),
                ('2016', '2016'), ('2015', '2015'), ('2014', '2014'), ('2013', '2013'),
                ('2012', '2012'), ('2011', '2011'), ('2010', '2010')]}
        },
        '3': {
            'area': {'label': '地区', 'options': [('', '全部'), ('大陆', '大陆'), ('香港', '香港'),
                ('美国', '美国'), ('台湾', '台湾'), ('韩国', '韩国'), ('日本', '日本')]},
            'year': {'label': '年份', 'options': [('', '全部'), ('2026', '2026'), ('2025', '2025'),
                ('2024', '2024'), ('2023', '2023'), ('2022', '2022'), ('2021', '2021'),
                ('2020', '2020'), ('2019', '2019')]}
        },
        '4': {
            'area': {'label': '地区', 'options': [('', '全部'), ('大陆', '大陆'), ('香港', '香港'),
                ('美国', '美国'), ('台湾', '台湾'), ('韩国', '韩国'), ('日本', '日本')]},
            'year': {'label': '年份', 'options': [('', '全部'), ('2026', '2026'), ('2025', '2025'),
                ('2024', '2024'), ('2023', '2023'), ('2022', '2022'), ('2021', '2021'),
                ('2020', '2020'), ('2019', '2019')]}
        }
    }

    def __init__(self):
        self.name = "看戏影院"
        self.host = self.HOST
        self.header = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
            "Referer": self.HOST + self.BASE,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def getName(self):
        return self.name

    def init(self, extend=""):
        """初始化"""
        pass

    def homeContent(self, filter):
        """首页分类和筛选配置"""
        classes = [{"type_name": name, "type_id": cid} for cid, name in self.CATS]
        filters = {}
        for cid, config in self.FILTERS.items():
            filters[cid] = []
            for key, value in config.items():
                filters[cid].append({
                    "key": key,
                    "name": value["label"],
                    "value": [{"n": name, "v": val} for val, name in value["options"]]
                })
        return {"class": classes, "filters": filters}

    def homeVideoContent(self):
        """首页推荐内容"""
        try:
            html = self._fetch("/")
            videos = self._parse_list(html)
            return {"list": videos[:30]}
        except Exception as e:
            print(f"首页加载失败: {e}")
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        """分类内容（含筛选）"""
        try:
            # 解析扩展参数
            ext = self._decode_ext(extend)
            cate = ext.get("cate", "")
            area = ext.get("area", "")
            year = ext.get("year", "")

            # 构建URL
            if cate or area or year:
                # 带筛选的tags页面
                segs = [cate or tid, area or "", "", "", "", "", "", "", "", "", "", year or ""]
                url = f"/tags/{'-'.join(segs)}.html?page={pg}"
            else:
                url = f"/list/{tid}.html?page={pg}"

            html = self._fetch(url)
            videos = self._parse_list(html)
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": 999,
                "limit": 30,
                "total": 999999,
            }
        except Exception as e:
            print(f"分类加载失败: {e}")
            return {"list": [], "page": int(pg), "pagecount": 0, "limit": 30, "total": 0}

    def detailContent(self, ids):
        """详情页解析"""
        try:
            vod_id = str(ids[0]).split("/")[0]
            url = f"/post/{vod_id}.html"
            html = self._fetch(url)
            detail = self._parse_detail(html, vod_id)

            if not detail:
                return {"list": []}

            # 构建播放源
            play_from = []
            play_url = []
            for line in detail.get("lines", []):
                if line.get("eps"):
                    play_from.append(line["name"])
                    play_url.append("#".join([f"{ep['name']}${ep['url']}" for ep in line["eps"]]))

            video = {
                "vod_id": vod_id,
                "vod_name": detail.get("title", ""),
                "vod_pic": detail.get("pic", ""),
                "vod_year": detail.get("year", ""),
                "vod_area": detail.get("area", ""),
                "vod_actor": detail.get("actor", ""),
                "vod_director": detail.get("director", ""),
                "vod_content": detail.get("desc", ""),
                "vod_play_from": "$$$".join(play_from) if play_from else "看戏影院",
                "vod_play_url": "$$$".join(play_url),
            }
            return {"list": [video]}
        except Exception as e:
            print(f"详情加载失败: {e}")
            return {"list": []}

    def searchContent(self, key, quick, pg=1):
        """搜索功能"""
        try:
            url = f"/search/{key}-------------.html"
            if pg > 1:
                url += f"?page={pg}"
            html = self._fetch(url)
            videos = self._parse_list(html)
            return {
                "list": videos,
                "page": int(pg),
                "pagecount": 999,
                "limit": 30,
                "total": 999999,
            }
        except Exception as e:
            print(f"搜索失败: {e}")
            return {"list": [], "page": int(pg), "pagecount": 0, "limit": 30, "total": 0}

    def playerContent(self, flag, id, vipFlags):
        """播放地址解析"""
        try:
            print(f"播放请求 - flag: {flag}, id: {id}")
            
            # 如果是完整URL，直接返回
            if id.startswith("http://") or id.startswith("https://"):
                print(f"直接返回完整URL: {id}")
                return {
                    "parse": 0,
                    "playUrl": "",
                    "url": id,
                    "header": self.header,
                }

            # 构建播放页URL
            # id格式可能是: /play/123.html 或 123 或 play/123.html
            if id.startswith("/"):
                play_url = id
            elif id.startswith("play/"):
                play_url = "/" + id
            else:
                play_url = f"/play/{id}.html"
            
            # 如果id包含.html则直接使用，否则添加.html
            if not id.endswith(".html") and not id.startswith("/play/"):
                play_url = f"/play/{id}.html"
            
            print(f"请求播放页: {play_url}")
            html = self._fetch(play_url)

            # 方法1: 匹配 var player_data = {...};
            match = re.search(r'var\s+player_data\s*=\s*(\{[\s\S]*?\});', html)
            if match:
                try:
                    player_data_str = match.group(1)
                    # 清理JavaScript注释和特殊字符
                    player_data_str = re.sub(r'//.*?$', '', player_data_str, flags=re.MULTILINE)
                    player_data_str = re.sub(r'/\*.*?\*/', '', player_data_str, flags=re.DOTALL)
                    player_data = json.loads(player_data_str)
                    print(f"解析到player_data: {player_data}")
                    
                    if player_data.get("encrypt") == 0 and player_data.get("url"):
                        real_url = player_data["url"]
                        if real_url.startswith("http"):
                            print(f"获取到播放地址: {real_url}")
                            return {
                                "parse": 0,
                                "playUrl": "",
                                "url": real_url,
                                "header": self.header,
                            }
                except Exception as e:
                    print(f"解析player_data失败: {e}")

            # 方法2: 匹配 iframe 中的 src
            iframe_match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html, re.I)
            if iframe_match:
                src = iframe_match.group(1)
                print(f"找到iframe src: {src}")
                if src.startswith("http"):
                    # 如果是解析器地址，需要处理
                    if "m3u8" in src or "mp4" in src:
                        return {
                            "parse": 0,
                            "playUrl": "",
                            "url": src,
                            "header": self.header,
                        }
                    else:
                        return {
                            "parse": 1,
                            "playUrl": src,
                            "url": "",
                            "header": self.header,
                        }

            # 方法3: 匹配视频源地址
            video_sources = [
                r'<video[^>]*src=["\']([^"\']+)["\']',
                r'source[^>]*src=["\']([^"\']+)["\']',
                r'data-video=["\']([^"\']+)["\']',
                r'data-url=["\']([^"\']+)["\']',
                r'url\s*[:=]\s*["\']([^"\']+)["\']',
                r'video\s*[:=]\s*["\']([^"\']+)["\']',
                r'"url"\s*:\s*"([^"]+)"',
                r'"link"\s*:\s*"([^"]+)"',
            ]
            
            for pattern in video_sources:
                match = re.search(pattern, html, re.I)
                if match:
                    video_url = match.group(1)
                    if video_url.startswith("http") and (".m3u8" in video_url or ".mp4" in video_url):
                        print(f"从页面匹配到视频地址: {video_url}")
                        return {
                            "parse": 0,
                            "playUrl": "",
                            "url": video_url,
                            "header": self.header,
                        }

            # 方法4: 尝试从script标签中提取
            script_matches = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
            for script in script_matches:
                # 查找m3u8或mp4链接
                url_matches = re.findall(r'["\']((?:https?:)?//[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', script)
                for url in url_matches:
                    if url.startswith("http"):
                        print(f"从script提取到播放地址: {url}")
                        return {
                            "parse": 0,
                            "playUrl": "",
                            "url": url,
                            "header": self.header,
                        }

            # 如果都没找到，返回播放页URL让系统自行处理
            print(f"未找到播放地址，返回播放页URL: {play_url}")
            return {
                "parse": 1,  # 让系统使用解析器
                "playUrl": self.host + play_url,
                "url": "",
                "header": self.header,
            }
            
        except Exception as e:
            print(f"播放解析失败: {e}")
            import traceback
            traceback.print_exc()
            return {"parse": 0, "playUrl": "", "url": ""}

    def isVideoFormat(self, url):
        """检查是否为视频格式"""
        video_formats = [".m3u8", ".mp4", ".avi", ".mkv", ".flv", ".ts"]
        return any(str(url).lower().endswith(fmt) for fmt in video_formats)

    def manualVideoCheck(self):
        pass

    def localProxy(self, params):
        return None

    # ---------- 内部方法 ----------

    def _fetch(self, path):
        """请求页面"""
        url = f"{self.host}{path}" if path.startswith("/") else path
        try:
            print(f"请求URL: {url}")
            resp = self.fetch(url, headers=self.header, timeout=15)
            if hasattr(resp, "text"):
                return resp.text
            if hasattr(resp, "content"):
                return resp.content.decode("utf-8", errors="ignore")
            return str(resp)
        except Exception as e:
            print(f"请求失败 {url}: {e}")
            raise

    def _parse_list(self, html):
        """解析列表页面，提取视频列表"""
        videos = []

        # 匹配视频卡片
        pattern = r'<a[^>]*class="[^"]*stui-vodlist__thumb[^"]*"[^>]*href="[^"]*/post/(\d+)\.html[^"]*"[^>]*>'
        for match in re.finditer(pattern, html):
            aid = match.group(1)
            # 提取标题
            title_match = re.search(r'title="([^"]+)"', match.group(0))
            title = title_match.group(1) if title_match else ""

            # 提取图片
            img_match = re.search(r'data-original="([^"]+)"', match.group(0))
            pic = img_match.group(1) if img_match else ""

            # 如果没有标题，从后面的h4中提取
            if not title:
                container = self._find_parent_container(html, match.start())
                if container:
                    title_match2 = re.search(r'<h4[^>]*class="[^"]*title[^"]*"[^>]*>.*?<a[^>]*>([^<]+)</a>', container, re.S)
                    if title_match2:
                        title = self._clean_text(title_match2.group(1))

            if not title:
                title = "未知影片"

            # 提取备注（集数/状态）
            remark = ""
            pic_text_match = re.search(r'<span[^>]*class="[^"]*pic-text[^"]*"[^>]*>([^<]+)</span>', match.group(0))
            if pic_text_match:
                remark = self._clean_text(pic_text_match.group(1))

            # 检查是否已存在
            if not any(v["vod_id"] == aid for v in videos):
                videos.append({
                    "vod_id": aid,
                    "vod_name": title,
                    "vod_pic": self._fix_img(pic),
                    "vod_remarks": remark,
                })

        return videos[:50]

    def _find_parent_container(self, html, pos):
        """查找包含指定位置的父容器"""
        before = html[:pos]
        last_box = before.rfind('<div class="stui-vodlist__box"')
        if last_box != -1:
            start = last_box
            depth = 0
            i = start
            while i < len(html):
                if html[i:i + 6] == '<div ':
                    depth += 1
                    i += 6
                elif html[i:i + 7] == '</div>':
                    depth -= 1
                    if depth == 0:
                        return html[start:i + 7]
                    i += 7
                else:
                    i += 1
        return ""

    def _parse_detail(self, html, vod_id):
        """解析详情页"""
        result = {
            "id": vod_id,
            "title": "",
            "pic": "",
            "year": "",
            "area": "",
            "type": "",
            "director": "",
            "actor": "",
            "status": "",
            "desc": "",
            "tags": [],
            "lines": [],
        }

        # 提取标题
        title_match = re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>', html, re.S)
        if title_match:
            result["title"] = self._clean_text(title_match.group(1))

        # 提取海报
        poster_match = re.search(r'<img[^>]*class="[^"]*stui-content__thumb[^"]*"[^>]*data-original="([^"]+)"', html)
        if poster_match:
            result["pic"] = self._fix_img(poster_match.group(1))

        # 提取详细信息
        data_items = re.findall(r'<div[^>]*class="[^"]*data[^"]*"[^>]*>(.*?)</div>', html, re.S)
        for item in data_items:
            text = self._clean_text(item)

            if "年份" in text:
                year_match = re.search(r'<a[^>]*>([^<]+)</a>', item)
                if year_match:
                    result["year"] = self._clean_text(year_match.group(1))

            if "类型" in text:
                type_match = re.search(r'<a[^>]*>([^<]+)</a>', item)
                if type_match:
                    result["type"] = self._clean_text(type_match.group(1))

            if "地区" in text:
                area_match = re.search(r'<a[^>]*>([^<]+)</a>', item)
                if area_match:
                    result["area"] = self._clean_text(area_match.group(1))

            if "导演" in text:
                dir_match = re.search(r'<a[^>]*>([^<]+)</a>', item)
                if dir_match:
                    result["director"] = self._clean_text(dir_match.group(1))

            if "状态" in text:
                status_match = re.search(r'<span[^>]*class="[^"]*data3[^"]*"[^>]*>([^<]+)</span>', item)
                if status_match:
                    result["status"] = self._clean_text(status_match.group(1))

            if "主演" in text:
                actor_match = re.search(r'<a[^>]*>([^<]+)</a>', item)
                if actor_match:
                    result["actor"] = self._clean_text(actor_match.group(1))

        # 提取简介
        desc_match = re.search(r'<div[^>]*class="[^"]*detail-content[^"]*"[^>]*>(.*?)</div>', html, re.S)
        if desc_match:
            result["desc"] = self._clean_text(desc_match.group(1))

        # 提取播放线路
        line_pattern = r'<div[^>]*class="[^"]*stui-vodlist__head[^"]*"[^>]*>.*?<h4[^>]*>([^<]+)</h4>.*?</div>.*?<ul[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>(.*?)</ul>'
        for match in re.finditer(line_pattern, html, re.S):
            line_name = self._clean_text(match.group(1))
            line_name = re.sub(r'iconfont', '', line_name)
            line_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', line_name).strip()
            if not line_name:
                line_name = "线路"

            eps_html = match.group(2)
            eps = []

            ep_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>'
            for ep_match in re.finditer(ep_pattern, eps_html):
                ep_href = ep_match.group(1)
                ep_name = self._clean_text(ep_match.group(2))
                if ep_href:
                    eps.append({"name": ep_name, "url": ep_href})

            if eps:
                result["lines"].append({"name": line_name, "eps": eps})

        # 如果没有找到线路，尝试备用匹配
        if not result["lines"]:
            playlist_match = re.search(r'<ul[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>(.*?)</ul>', html, re.S)
            if playlist_match:
                eps = []
                ep_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>'
                for ep_match in re.finditer(ep_pattern, playlist_match.group(1)):
                    ep_href = ep_match.group(1)
                    ep_name = self._clean_text(ep_match.group(2))
                    if ep_href:
                        eps.append({"name": ep_name, "url": ep_href})
                if eps:
                    result["lines"].append({"name": "默认线路", "eps": eps})

        # 构建标签
        tags = []
        if result["year"]:
            tags.append(result["year"])
        if result["area"]:
            tags.append(result["area"])
        if result["type"]:
            tags.append(result["type"])
        if result["status"]:
            tags.append(result["status"])
        result["tags"] = tags

        return result

    def _clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\u3000', ' ').strip()
        return text

    def _fix_img(self, url):
        """修正图片URL"""
        if not url:
            return ""
        url = url.strip()
        if url.startswith("//"):
            url = "https:" + url
        if url.startswith("http://"):
            url = "https://" + url[7:]
        return url

    def _decode_ext(self, raw):
        """解码扩展参数"""
        if not raw:
            return {}
        if isinstance(raw, dict):
            return raw
        try:
            decoded = base64.b64decode(str(raw)).decode("utf-8")
            return json.loads(decoded)
        except:
            pass
        try:
            padded = str(raw) + "=" * ((4 - len(str(raw)) % 4) % 4)
            decoded = base64.urlsafe_b64decode(padded).decode("utf-8")
            return json.loads(decoded)
        except:
            pass
        return {}


if __name__ == "__main__":
    spider = Spider()
    spider.init()
    print("看戏影院爬虫初始化成功")