import atexit
import json
import os
import pickle
import time
from typing import Dict, Any

from fastmcp import FastMCP
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver


class XiaohongshuMCP:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.is_logged_in = False
        self.session_file = "xiaohongshu_session.pkl"
        self.cookies_file = "xiaohongshu_cookies.json"

    def _setup_driver(self, load_session: bool = True):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')
        self.driver = webdriver.Chrome(options=chrome_options, service=Service(CHROME_DRIVER_PATH))
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)


    def _ensure_driver(self):
        """确保浏览器驱动已初始化"""
        if self.driver is None or not self._is_browser_alive():
            if self.driver:
                self.driver.quit()  # 先关闭旧实例
            self._setup_driver()

    def _is_browser_alive(self):
        """检查浏览器实例是否仍然有效"""
        try:
            # 尝试获取当前URL来验证浏览器是否仍然响应
            _ = self.driver.current_url
            return True
        except:
            return False

    def _save_session(self):
        """保存登录会话信息"""
        try:
            # 保存cookies
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            # 保存会话状态
            session_data = {
                'is_logged_in': self.is_logged_in,
                'current_url': self.driver.current_url,
                'user_agent': self.driver.execute_script("return navigator.userAgent;"),
                'timestamp': time.time()
            }

            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)

            print("登录状态已保存")

        except Exception as e:
            print(f"保存会话失败: {str(e)}")

    def _load_session(self):
        """加载登录会话信息"""
        try:
            # 检查会话文件是否存在且未过期（24小时）
            if os.path.exists(self.session_file):
                with open(self.session_file, 'rb') as f:
                    session_data = pickle.load(f)

                # 检查会话是否过期（24小时）
                if time.time() - session_data.get('timestamp', 0) > 86400:
                    print("会话已过期")
                    return False

                # 访问小红书首页
                self.driver.get("https://www.xiaohongshu.com/")
                time.sleep(2)

                # 加载cookies
                if os.path.exists(self.cookies_file):
                    with open(self.cookies_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)

                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as e:
                            continue

                # 刷新页面使cookies生效
                self.driver.refresh()
                time.sleep(3)

                # 检查登录状态
                if self._check_login_status():
                    self.is_logged_in = session_data.get('is_logged_in', False)
                    print("会话加载成功，已自动登录")
                    return True

            return False

        except Exception as e:
            print(f"加载会话失败: {str(e)}")
            return False

    def _check_login_status(self):
        """检查当前登录状态"""
        try:

            # 检查是否存在登录按钮（如果存在说明未登录）
            login_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".login-btn, .sign-in, [data-v-*='登录']")

            # 检查是否存在用户头像（如果存在说明已登录）
            avatar_elements = self.driver.find_elements(By.CSS_SELECTOR, ".reds-avatar")

            # 检查是否存在用户相关的元素
            user_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-v-*='个人中心'], .user-menu")

            is_logged_in = len(avatar_elements) > 0 or len(user_elements) > 0 or len(login_buttons) == 0

            if is_logged_in:
                self.is_logged_in = True
                print("检测到已登录状态")
            else:
                self.is_logged_in = False
                print("检测到未登录状态")

            return is_logged_in

        except Exception as e:
            print(f"检查登录状态失败: {str(e)}")
            return False

    def _clear_session(self):
        """清除保存的会话信息"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
            # 注意：不删除用户数据目录，因为它可能包含其他重要数据
            print("会话信息已清除")
        except Exception as e:
            print(f"清除会话失败: {str(e)}")

    async def _close_browser(self) -> Dict[str, Any]:
        """
        关闭浏览器

        Returns:
            关闭结果
        """
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.is_logged_in = False

            return {"success": True, "message": "浏览器已关闭"}

        except Exception as e:
            return {"success": False, "message": f"关闭浏览器失败: {str(e)}"}


# 创建MCP服务实例
mcp = FastMCP("Xiaohongshu")
xiaohongshu = XiaohongshuMCP()
@atexit.register
def cleanup():
    if xiaohongshu.driver:
        xiaohongshu.driver.quit()
@mcp.tool()
async def scroll():
    """
    滚动页面

    Returns:
        操作结果
    """
    xiaohongshu.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    return {"success": True, "message": "滚动完成"}


@mcp.tool()
async def login() -> Dict[str, Any]:
    """
    手动登录小红书

    Returns:
        登录结果
    """
    try:
        xiaohongshu._ensure_driver()
        # 访问小红书登录页面
        xiaohongshu.driver.get("https://www.xiaohongshu.com/")
        time.sleep(2)

        # 等待登录成功（检查页面跳转或特定元素出现）
        try:
            xiaohongshu.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".reds-avatar"))
                )
            )
            xiaohongshu.is_logged_in = True
            xiaohongshu._save_session()
            return {"success": True, "message": "登录成功"}
        except TimeoutException:
            return {"success": False, "message": "登录超时，请检查是否完成登录"}

    except Exception as e:
        return {"success": False, "message": f"登录失败: {str(e)}"}


@mcp.tool()
async def get_current_page_articles() -> Dict[str, Any]:
    """
    获取当前页面的文章列表，可以配合页面滚动工具使用

    Returns:
        当前页面文章列表，文章信息包括：标题、作者、文章链接、点赞数
    """
    try:
        xiaohongshu._ensure_driver()

        if not xiaohongshu.is_logged_in:
            ok = xiaohongshu._load_session()
            if not ok:
                return {"success": False, "message": "请先登录"}

        # 获取文章列表
        articles = []
        article_elements = xiaohongshu.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".note-item"))
        )

        for i, element in enumerate(article_elements):
            try:
                # 提取文章信息
                title_elem = element.find_element(By.CSS_SELECTOR, ".footer .title")
                title = title_elem.text.strip()

                # 获取链接
                link_elem = element.find_element(By.CSS_SELECTOR, ".cover, .mask, .ld")
                link = link_elem.get_attribute("href")

                # 获取作者信息
                author_elem = element.find_element(By.CSS_SELECTOR, ".author .name")
                author = author_elem.text.strip()

                # 获取点赞数
                like_elem = element.find_element(By.CSS_SELECTOR, ".footer .like-wrapper .count")
                like = like_elem.text.strip()

                articles.append({
                    "title": title,
                    "author": author,
                    "link": link,
                    "like": like,
                })

            except Exception as e:
                continue

        return {
            "success": True,
            "articles": articles,
            "count": len(articles)
        }

    except Exception as e:
        return {"success": False, "message": f"搜索失败: {str(e)}"}


@mcp.tool()
async def search_articles(keyword: str) -> Dict[str, Any]:
    """
    搜索小红书文章

    Args:
        keyword: 搜索关键词

    Returns:
        搜索文章列表，文章信息包括：标题、作者、文章链接、点赞数
    """
    try:
        xiaohongshu._ensure_driver()

        if not xiaohongshu.is_logged_in:
            ok = xiaohongshu._load_session()
            if not ok:
                return {"success": False, "message": "请先登录"}

        # 访问搜索页面
        xiaohongshu.driver.get(f"https://www.xiaohongshu.com/search_result?keyword={keyword}")
        time.sleep(2)
        # 获取文章列表
        articles = []
        article_elements = xiaohongshu.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".note-item"))
        )

        for i, element in enumerate(article_elements):
            try:
                # 提取文章信息
                title_elem = element.find_element(By.CSS_SELECTOR, ".footer .title")
                title = title_elem.text.strip()

                # 获取链接
                link_elem = element.find_element(By.CSS_SELECTOR, ".cover, .mask, .ld")
                link = link_elem.get_attribute("href")

                # 获取作者信息
                author_elem = element.find_element(By.CSS_SELECTOR, ".author .name")
                author = author_elem.text.strip()

                # 获取点赞数
                like_elem = element.find_element(By.CSS_SELECTOR, ".footer .like-wrapper .count")
                like = like_elem.text.strip()

                articles.append({
                    "title": title,
                    "author": author,
                    "link": link,
                    "like": like,
                })

            except Exception as e:
                continue

        return {
            "success": True,
            "keyword": keyword,
            "articles": articles,
            "count": len(articles)
        }

    except Exception as e:
        return {"success": False, "message": f"搜索失败: {str(e)}"}


@mcp.tool()
async def get_article_content(article_url: str) -> Dict[str, Any]:
    """
    查看文章内容

    Args:
        article_url: 文章访问链接

    Returns:
        文章内容
    """
    try:
        xiaohongshu._ensure_driver()

        if not xiaohongshu.is_logged_in:
            ok = xiaohongshu._load_session()
            if not ok:
                return {"success": False, "message": "请先登录"}

        # 访问文章页面
        xiaohongshu.driver.get(article_url)
        time.sleep(3)

        # 获取评论内容
        content_elements = xiaohongshu.driver.find_elements(By.CSS_SELECTOR, ".desc .note-text")
        for i, element in enumerate(content_elements):
            content = element.text.strip()
            return {"success": True, "content": content}

    except Exception as e:
        return {"success": False, "message": f"搜索失败: {str(e)}"}


@mcp.tool()
async def view_article_comments(article_url: str, limit: int = 20) -> Dict[str, Any]:
    """
    查看文章一级评论

    Args:
        article_url: 文章访问链接
        limit: 获取评论数量限制

    Returns:
        评论列表
    """
    try:
        xiaohongshu._ensure_driver()

        if not xiaohongshu.is_logged_in:
            ok = xiaohongshu._load_session()
            if not ok:
                return {"success": False, "message": "请先登录"}

        # 访问文章页面
        xiaohongshu.driver.get(article_url)
        time.sleep(3)
        # 滚动页面加载更多评论
        xiaohongshu.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # 获取评论内容
        comments = []

        # 查找评论区域
        comment_elements = xiaohongshu.driver.find_elements(By.CSS_SELECTOR, ".comments-container .list-container .parent-comment")

        for i, element in enumerate(comment_elements[:limit]):
            try:
                # 获取评论者用户名
                username_elem = element.find_element(By.CSS_SELECTOR, ".author")
                username = username_elem.text.strip()

                # 获取评论内容
                content_elem = element.find_element(By.CSS_SELECTOR, ".content, .note-text")
                content = content_elem.text.strip()

                comments.append({
                    "username": username,
                    "content": content,
                })

            except Exception as e:
                continue

        return {
            "success": True,
            "article_url": article_url,
            "comments": comments,
            "count": len(comments)
        }

    except Exception as e:
        return {"success": False, "message": f"获取评论失败: {str(e)}"}


@mcp.tool()
async def post_comment(article_url: str, comment_text: str) -> Dict[str, Any]:
    """
    在文章下发表评论

    Args:
        article_url: 文章访问链接
        comment_text: 评论内容

    Returns:
        评论发表结果
    """
    try:
        xiaohongshu._ensure_driver()

        if not xiaohongshu.is_logged_in:
            ok = xiaohongshu._load_session()
            if not ok:
                return {"success": False, "message": "请先登录"}

        # 访问文章页面
        xiaohongshu.driver.get(article_url)
        time.sleep(3)

        # 查找评论输入框
        input_box = xiaohongshu.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".input-box .content-edit"))
        )

        # 点击输入框并输入评论
        input_box.click()
        time.sleep(1)
        comment_input = xiaohongshu.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".input-box .content-edit .content-input"))
        )
        comment_input.send_keys(comment_text)

        # 查找并点击发表按钮
        submit_btn = xiaohongshu.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '发表') or contains(text(), '发送')]"))
        )
        submit_btn.click()

        # 等待评论发表完成
        time.sleep(3)

        return {
            "success": True,
            "message": "评论发表成功",
            "comment": comment_text
        }

    except Exception as e:
        return {"success": False, "message": f"评论发表失败: {str(e)}"}



@mcp.tool()
async def close_browser() -> Dict[str, Any]:
    """
    关闭浏览器

    Returns:
        关闭结果
    """
    try:
        if xiaohongshu.driver:
            xiaohongshu.driver.quit()
            xiaohongshu.driver = None
            xiaohongshu.is_logged_in = False

        return {"success": True, "message": "浏览器已关闭"}

    except Exception as e:
        return {"success": False, "message": f"关闭浏览器失败: {str(e)}"}


if __name__ == "__main__":
    # 运行MCP服务
    mcp.run(transport='stdio')

