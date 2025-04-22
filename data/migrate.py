# Run this script to migrate the data

from neo4j import GraphDatabase
import json
import re


DATA = "chung.json"
CREATE_CHAPTER_CYPHER = """MATCH (b:BOOK {{name: "Bộ luật dân sự"}})
CREATE (b)-[:HAS]->(c:CHAPTER {{name: "{name}"}})"""
CREATE_ARTICLE_CYPHER = """MATCH (c:CHAPTER {{name: "{chapter_name}"}})
CREATE (c)-[:HAS]->(a:ARTICLE {{name: "{article_name}", title: "{article_title}", content: "{article_content}"}})"""
CREATE_REF_CYPHER = """MATCH (a:ARTICLE {{name: "{article_name}"}}), (b:ARTICLE {{name: "{ref_name}"}})
CREATE (a)-[:REFERS_TO]->(b)"""

db = GraphDatabase.driver("bolt://localhost:7687")


def find_article_ref(content: str) -> list[str]:
    pattern = r"(?i)Điều\s+\d+"
    return re.findall(pattern, content)


if __name__ == "__main__":
    # 1. Read the JSON file
    with open(DATA, 'r', encoding="utf-8") as f:
        data = json.load(f)

    # 2. Format the data
    law_content = data['Luat']['content']['luat dan su']
    format_law_content = {}
    for content in law_content.values():
        # Kiểm tra nếu content là các Mục
        if 'Mục 1' in content['content'].keys():
            for c in content['content'].values():
                # Kiểm tra nếu tiêu đề đã tồn tại trong format_law_content
                if c['title'] not in format_law_content:
                    format_law_content[c['title']] = {}
                # Nếu tiêu đề đã tồn tại, thêm nội dung vào danh sách
                for k, v in c['dieu'].items():
                    format_law_content[c['title']][k] = v
                    format_law_content[c['title']][k]["ref"] = find_article_ref(
                        v['content'])
        # Nếu không, thêm tiêu đề của content vào danh sách
        else:
            if content['title'] not in format_law_content:
                format_law_content[content['title']] = {}
            # Nếu tiêu đề đã tồn tại, thêm nội dung vào danh sách
            for k, v in content['content'].items():
                format_law_content[content['title']][k] = v
                format_law_content[content['title']
                                   ][k]["ref"] = find_article_ref(v['content'])

    # 3. Create a master node
    db.execute_query("CREATE (b:BOOK {name: 'Bộ luật dân sự'})")

    # 4. Add chapters and articles to the database
    for chaper, articles in format_law_content.items():
        # Create a chapter node
        db.execute_query(CREATE_CHAPTER_CYPHER.format(name=chaper))
        # Create article nodes and relationships
        for article, content in articles.items():
            db.execute_query(CREATE_ARTICLE_CYPHER.format(
                chapter_name=chaper,
                article_name=article,
                article_title=content['title'],
                article_content=content['content']
            ))

    # 5. Add article references to the database
    for chaper, articles in format_law_content.items():
        for article, content in articles.items():
            for ref in set(content['ref']):
                # Create a reference relationship between articles
                db.execute_query(CREATE_REF_CYPHER.format(
                    article_name=article,
                    ref_name=ref
                ))
