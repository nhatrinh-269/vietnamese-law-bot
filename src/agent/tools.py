# Tool definition
import re
from typing import Annotated
from llama_index.core.tools import FunctionTool
from configs.neo4j import db


def get_chapters() -> list[str]:
    """Truy vấn tất cả các tên chương có trong bộ luật."""
    query = "MATCH (c:CHAPTER) RETURN c.name AS chapter_name"
    result = db.execute_query(query)[0]
    return [record['chapter_name'] for record in result]


def get_articles(
    chapter_names: Annotated[list[str],
                             "Danh sách tên chương để truy vấn các điều trong chương đó."]
) -> list[str]:
    """Truy vấn tất cả các điều trong các chương được chỉ định."""
    query = "MATCH (c:CHAPTER)-[:HAS]->(a:ARTICLE) WHERE c.name IN $chapter_names RETURN a.name AS article_name, a.title AS article_title"
    result = db.execute_query(query, chapter_names=chapter_names)[0]
    return [f"{record['article_name']}: {record['article_title']}" for record in result]


def get_articles_content_and_references(
    article_names: Annotated[list[str],
                             "Danh sách tên điều để truy vấn nội dung và các điều tham chiếu."]
) -> dict[str, str]:
    """Truy vấn nội dung của các điều và tham chiếu của các điều đó."""
    query = """
    MATCH (a:ARTICLE {name: $article})
    OPTIONAL MATCH (a)-[:REFERS_TO]->(ref:ARTICLE)
    RETURN a AS content, collect(ref) AS references
    """
    results = []

    for article in article_names:
        # Format article name to match the database format
        match = re.match(r"(Điều\s+\d+)", article.strip())
        if not match:
            continue
        article_name = match.group(1)

        result = db.execute_query(query, article=article_name)[0]
        if result:
            content = result[0]['content']
            references = [
                f"{ref['name']}: {ref['content']}" for ref in result[0]['references']]
            results.append({
                'content': f"{content['name']}: {content['content']}",
                'references': references
            })

    return results


def get_articles_content(
    article_names: Annotated[list[str],
                             "Danh sách tên điều để truy vấn nội dung."]
) -> dict[str, str]:
    """Truy vấn nội dung của các điều."""
    query = """
    MATCH (a:ARTICLE {name: $article})
    RETURN a AS content
    """
    results = []

    for article in article_names:
        # Format article name to match the database format
        match = re.match(r"(Điều\s+\d+)", article.strip())
        if not match:
            continue
        article_name = match.group(1)

        result = db.execute_query(query, article=article_name)[0]
        if result:
            content = result[0]['content']
            results.append({
                'content': f"{content['name']}: {content['content']}",
            })

    return results


get_chapters_tool = FunctionTool.from_defaults(
    fn=get_chapters,
    name="get_chapters",
    description="Truy vấn tất cả các tên chương có trong bộ luật. Bạn cần sử dụng công cụ này để lấy danh sách các chương trước khi sử dụng công cụ get_articles.",
)

get_articles_tool = FunctionTool.from_defaults(
    fn=get_articles,
    name="get_articles",
    description="Truy vấn tất cả các điều trong các chương được chỉ định. Bạn cần cung cấp danh sách tên chương để truy vấn.",
)

get_articles_content_and_references_tool = FunctionTool.from_defaults(
    fn=get_articles_content_and_references,
    name="get_article_content_and_references",
    description="Truy vấn nội dung và các tham chiếu của các điều. Bạn cần cung cấp tên điều để truy vấn. Ví dụ: 'Điều 1', 'Điều 2', ...",
)

get_articles_content_tool = FunctionTool.from_defaults(
    fn=get_articles_content,
    name="get_article_content",
    description="Truy vấn nội dung của các điều. Bạn cần cung cấp tên điều để truy vấn. Ví dụ: 'Điều 1', 'Điều 2', ...",
)
