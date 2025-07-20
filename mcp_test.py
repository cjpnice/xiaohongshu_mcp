import asyncio
from mcp_server import search_articles, login, scroll, get_current_page_articles, get_article_content, \
    view_article_comments, post_comment


async def main():
    # login_result = await login.run({})
    # print(f"登录结果: {login_result}")
    results = await search_articles.run({"keyword": "领克03"})
    print(f"搜索结果: {results}")
    await scroll.run({})
    results = await get_current_page_articles.run({})
    print(f"搜索结果: {results}")
    results = await get_article_content.run({"article_url": "https://www.xiaohongshu.com/explore/6878d94b000000001202ed7e?xsec_token=AB7HdBDEtxBY_U-5Gl6Wvq4z-gASesVELTfdsXqs1DZbA=&xsec_source=pc_search"})
    print(f"搜索结果: {results}")
    results = await view_article_comments.run({"article_url":"https://www.xiaohongshu.com/explore/687314bd000000001c031232?xsec_token=ABs0_Kwq9CFk5SSIU5bBT9hY6MWenpdbqZOxvbaKDuD6I=&xsec_source=pc_search", "limit": 20})
    print(f"搜索结果: {results}")
    results = await post_comment.run({"article_url":"https://www.xiaohongshu.com/explore/687314bd000000001c031232?xsec_token=ABs0_Kwq9CFk5SSIU5bBT9hY6MWenpdbqZOxvbaKDuD6I=&xsec_source=pc_search", "comment_text": "好漂亮"})
    print(f"搜索结果: {results}")



if __name__ == "__main__":
    asyncio.run(main())

