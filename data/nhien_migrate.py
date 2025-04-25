from neo4j import GraphDatabase
import json
from pathlib import Path
import re


class LawGraphImporter:
    def __init__(self, uri, json_file):
        self.driver = GraphDatabase.driver(uri)
        self.data = json.loads(Path(json_file).read_text(encoding="utf-8"))
        self.article_refs: dict[str, list[str]] = {}

    def find_article_refs(self, content: str) -> list[str]:
        pattern = r"(?i)Điều\s+\d+"
        matches = re.findall(pattern, content)
        return [m.strip().capitalize() for m in matches]

    def import_data(self):
        root = self.data.get("Luat", {})
        root_title = root.get("title", "Luật Việt Nam")

        with self.driver.session(database='viphamhanhchinh') as ses:
            ses.execute_write(self.create_root, root_title)

            for law_key, law_data in (root.get("content") or {}).items():
                if not isinstance(law_data, dict):
                    continue

                law_title = law_data.get("title", law_key)
                ses.execute_write(self.create_law, law_key, law_title)
                ses.execute_write(self.rel_root_to_law, root_title, law_key)

                chapters = law_data.get("content") or {
                    k: v for k, v in law_data.items() if k != "title"
                }

                for chap_key, chap_data in chapters.items():
                    chap_title = chap_data.get("title", chap_key)
                    ses.execute_write(self.create_chapter,
                                      law_key, chap_key, chap_title)
                    ses.execute_write(
                        self.rel_law_to_chapter, law_key, chap_key)

                    self._walk_level(
                        ses,
                        law_key,
                        chap_key,
                        chap_data.get("content")
                        or chap_data.get("muc")
                        or chap_data.get("dieu")
                        or {},
                    )

            # Tạo REFERS_TO sau khi các node đã được tạo
            for article, refs in self.article_refs.items():
                key, law = article.split(":")
                for ref in set(refs):
                    ref = ref.strip().capitalize()
                    ses.execute_write(
                        self.rel_dieu_to_dieu, law, key, ref, "REFERS_TO"
                    )

    def close(self):
        self.driver.close()

    def _walk_level(self, ses, law, chap, node_dict, parent_type=None, parent_title=None):
        for k, v in node_dict.items():
            if k.startswith("Mục"):
                muc_title = v.get("title", k)
                ses.execute_write(self.create_muc, law, chap, muc_title)
                target_rel = "HAS_MUC" if parent_type is None else "HAS_TIEUMUC"

                if parent_type == "Muc":
                    ses.execute_write(self.rel_muc_to_tieumuc, law,
                                      chap, parent_title, muc_title, target_rel)
                elif parent_type is None:
                    ses.execute_write(self.rel_chapter_to_node,
                                      law, chap, muc_title, target_rel)

                self._walk_level(
                    ses,
                    law,
                    chap,
                    v.get("tieu_muc") or v.get("dieu") or {},
                    parent_type="Muc",
                    parent_title=muc_title,
                )

            elif k.startswith("Tiểu mục"):
                tm_title = v.get("title", k)
                ses.execute_write(self.create_tieumuc, law, chap, tm_title)

                if parent_type == "Muc":
                    ses.execute_write(self.rel_muc_to_tieumuc, law,
                                      chap, parent_title, tm_title, "HAS_TIEUMUC")
                elif parent_type == "TieuMuc":
                    ses.execute_write(
                        self.rel_tieumuc_to_tieumuc, law, chap, parent_title, tm_title, "HAS_SUBTM")

                self._walk_level(
                    ses,
                    law,
                    chap,
                    v.get("dieu") or {},
                    parent_type="TieuMuc",
                    parent_title=tm_title,
                )

            elif k.startswith("Điều"):
                dieu_match = re.search(r"\d+", k)
                dieu_number = f"Điều {dieu_match.group()}" if dieu_match else k
                d_title = v.get("title", k)
                d_content = v.get("content") if isinstance(v, dict) else str(v)

                d_refs = self.find_article_refs(d_content)
                if d_refs:
                    self.article_refs[f"{dieu_number}:{law}"] = d_refs

                print(f"Creating node Dieu: {dieu_number}, Title: {d_title}")
                ses.execute_write(self.create_dieu, law, chap,
                                  dieu_number, d_title, d_content)

                if parent_type == "Muc":
                    ses.execute_write(self.rel_muc_to_dieu, law,
                                      chap, parent_title, d_title, "HAS_DIEU")
                elif parent_type == "TieuMuc":
                    ses.execute_write(self.rel_tieumuc_to_dieu,
                                      law, chap, parent_title, d_title, "HAS_DIEU")
                else:
                    ses.execute_write(self.rel_chapter_to_node,
                                      law, chap, d_title, "HAS_DIEU")

    # --- NODE ---
    @staticmethod
    def create_root(tx, title):
        tx.run("MERGE (:Root {title:$t})", t=title)

    @staticmethod
    def create_law(tx, key, title):
        tx.run("MERGE (l:Law {key:$k}) SET l.title=$t", k=key, t=title)

    @staticmethod
    def create_chapter(tx, law, chap, title):
        tx.run(
            "MERGE (c:Chapter {law:$l, key:$k}) SET c.title=$t", l=law, k=chap, t=title)

    @staticmethod
    def create_muc(tx, law, chap, title):
        tx.run("MERGE (:Muc {law:$l, parent:$c, title:$t})",
               l=law, c=chap, t=title)

    @staticmethod
    def create_tieumuc(tx, law, chap, title):
        tx.run(
            "MERGE (:TieuMuc {law:$l, parent:$c, title:$t})", l=law, c=chap, t=title)

    @staticmethod
    def create_dieu(tx, law, chap, dieu_number, title, content):
        tx.run("""
            MERGE (d:Dieu {law:$l, parent:$c, dieu_number:$n})
            SET d.title = $t, d.content = $ct
            """, l=law, c=chap, n=dieu_number, t=title, ct=content)

    # --- REL ---
    @staticmethod
    def rel_root_to_law(tx, root_title, law_key):
        tx.run("""MATCH (r:Root {title:$r}),(l:Law {key:$k})
                  MERGE (r)-[:HAS_LAW]->(l)""", r=root_title, k=law_key)

    @staticmethod
    def rel_law_to_chapter(tx, law_key, chap_key):
        tx.run("""MATCH (l:Law {key:$k}),(c:Chapter {law:$k,key:$c})
                  MERGE (l)-[:HAS_CHAPTER]->(c)""", k=law_key, c=chap_key)

    @staticmethod
    def rel_chapter_to_node(tx, law, chap, node_title, rel):
        tx.run(f"""MATCH (c:Chapter {{law:$l,key:$c}}),
                          (n {{law:$l,parent:$c,title:$t}})
                   MERGE (c)-[:{rel}]->(n)""", l=law, c=chap, t=node_title)

    @staticmethod
    def rel_muc_to_tieumuc(tx, law, chap, muc_title, tm_title, rel):
        tx.run(f"""MATCH (m:Muc {{law:$l,parent:$c,title:$m}}),
                          (t:TieuMuc {{law:$l,parent:$c,title:$tm}})
                   MERGE (m)-[:{rel}]->(t)""", l=law, c=chap, m=muc_title, tm=tm_title)

    @staticmethod
    def rel_muc_to_dieu(tx, law, chap, muc_title, dieu_title, rel):
        tx.run(f"""MATCH (m:Muc {{law:$l,parent:$c,title:$m}}),
                          (d:Dieu {{law:$l,parent:$c,title:$d}})
                   MERGE (m)-[:{rel}]->(d)""", l=law, c=chap, m=muc_title, d=dieu_title)

    @staticmethod
    def rel_tieumuc_to_tieumuc(tx, law, chap, parent_tm, child_tm, rel):
        tx.run(f"""MATCH (p:TieuMuc {{law:$l,parent:$c,title:$p}}),
                          (ch:TieuMuc {{law:$l,parent:$c,title:$ch}})
                   MERGE (p)-[:{rel}]->(ch)""", l=law, c=chap, p=parent_tm, ch=child_tm)

    @staticmethod
    def rel_tieumuc_to_dieu(tx, law, chap, tm_title, dieu_title, rel):
        tx.run(f"""MATCH (t:TieuMuc {{law:$l,parent:$c,title:$tm}}),
                          (d:Dieu {{law:$l,parent:$c,title:$d}})
                   MERGE (t)-[:{rel}]->(d)""", l=law, c=chap, tm=tm_title, d=dieu_title)

    @staticmethod
    def rel_dieu_to_dieu(tx, law, article_number, ref_number, rel):
        print(f"[REFERS_TO] {article_number} -> {ref_number} (Law: {law})")
        tx.run(f"""MATCH (a:Dieu {{dieu_number:$a, law:$l}}),
                          (b:Dieu {{dieu_number:$b, law:$l}})
                   MERGE (a)-[:{rel}]->(b)""", a=article_number, b=ref_number, l=law)


if __name__ == "__main__":
    uri = "bolt://75.101.186.147:7687"
    # user = "neo4j"
    # password = "factories-class-researcher"
    json_file = "/home/nhienhoang/FPT_work/law/dataset/chung (1).json"

    imp = LawGraphImporter(uri, json_file)
    imp.import_data()
    imp.close()
