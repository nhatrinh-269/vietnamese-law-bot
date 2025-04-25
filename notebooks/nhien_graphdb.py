from neo4j import GraphDatabase, basic_auth
import json
from pathlib import Path
import re


class LawGraphImporter:
    def __init__(self, uri, user, password, json_file):
        self.driver = GraphDatabase.driver(
            uri, auth=basic_auth(user, password))
        self.data = json.loads(Path(json_file).read_text(encoding="utf-8"))

        # Article references to link to other articles
        self.article_refs: dict[str, list[str]] = {}

    def find_article_refs(self, content: str) -> list[str]:
        pattern = r"(?i)Điều\s+\d+"
        return re.findall(pattern, content)

    # ---------- API ----------
    def import_data(self):
        root = self.data.get("Luat", {})
        root_title = root.get("title", "Luật Việt Nam")

        with self.driver.session() as ses:
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

            # At the end of create nodes, create relationships for article references
            for article, refs in self.article_refs.items():
                key, law = article.split(":")
                for ref in set(refs):
                    # Create a relationship between the article and the referenced article
                    ses.execute_write(
                        self.rel_dieu_to_dieu, law, key, ref, "REFERS_TO"
                    )

    def close(self):
        self.driver.close()

    # ---------- Đệ quy ----------
    def _walk_level(self, ses, law, chap, node_dict, parent_type=None, parent_title=None):
        """
        Duyệt Mục → Tiểu mục → Điều ở mọi độ sâu.
        parent_type: None | 'Muc' | 'TieuMuc'
        """

        for k, v in node_dict.items():
            # --------- MỤC ---------
            if k.startswith("Mục"):
                muc_title = v.get("title", k)
                ses.execute_write(self.create_muc, law, chap, muc_title)
                target_rel = "HAS_MUC" if parent_type is None else "HAS_TIEUMUC"
                if parent_type == "Muc":   # Tiểu mục lồng Mục (hiếm)
                    ses.execute_write(self.rel_muc_to_tieumuc, law,
                                      chap, parent_title, muc_title, target_rel)
                elif parent_type is None:
                    ses.execute_write(self.rel_chapter_to_node,
                                      law, chap, muc_title, target_rel)

                # Đệ quy xuống Tiểu mục hoặc Điều
                self._walk_level(
                    ses,
                    law,
                    chap,
                    v.get("tieu_muc") or v.get("dieu") or {},
                    parent_type="Muc",
                    parent_title=muc_title,
                )

            # --------- TIỂU MỤC ---------
            elif k.startswith("Tiểu mục"):
                tm_title = v.get("title", k)
                ses.execute_write(self.create_tieumuc, law, chap, tm_title)
                if parent_type == "Muc":
                    ses.execute_write(
                        self.rel_muc_to_tieumuc, law, chap, parent_title, tm_title, "HAS_TIEUMUC"
                    )
                elif parent_type == "TieuMuc":  # lồng sâu hơn (hiếm)
                    ses.execute_write(
                        self.rel_tieumuc_to_tieumuc, law, chap, parent_title, tm_title, "HAS_SUBTM"
                    )

                # Đệ quy xuống sâu hơn
                self._walk_level(
                    ses,
                    law,
                    chap,
                    v.get("dieu") or {},
                    parent_type="TieuMuc",
                    parent_title=tm_title,
                )

            # --------- ĐIỀU ---------
            elif k.startswith("Điều"):
                d_title = k
                d_content = v.get("content") if isinstance(v, dict) else str(v)

                # Find the article references in the content
                d_refs = self.find_article_refs(d_content)
                if d_refs:
                    self.article_refs[f"{k}:{law}"] = d_refs

                ses.execute_write(self.create_dieu, law,
                                  chap, d_title, d_content)

                if parent_type == "Muc":
                    ses.execute_write(
                        self.rel_muc_to_dieu, law, chap, parent_title, d_title, "HAS_DIEU"
                    )
                elif parent_type == "TieuMuc":
                    ses.execute_write(
                        self.rel_tieumuc_to_dieu, law, chap, parent_title, d_title, "HAS_DIEU"
                    )
                else:  # trực tiếp dưới Chương
                    ses.execute_write(
                        self.rel_chapter_to_node, law, chap, d_title, "HAS_DIEU"
                    )

    # ---------- NODE ----------
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
    def create_dieu(tx, law, chap, title, content):
        tx.run(
            """MERGE (d:Dieu {law:$l, parent:$c, title:$t})
               SET d.content=$ct""",
            l=law,
            c=chap,
            t=title,
            ct=content,
        )

    # ---------- REL ----------
    @staticmethod
    def rel_root_to_law(tx, root_title, law_key):
        tx.run(
            """MATCH (r:Root {title:$r}),(l:Law {key:$k})
               MERGE (r)-[:HAS_LAW]->(l)""",
            r=root_title,
            k=law_key,
        )

    @staticmethod
    def rel_law_to_chapter(tx, law_key, chap_key):
        tx.run(
            """MATCH (l:Law {key:$k}),(c:Chapter {law:$k,key:$c})
               MERGE (l)-[:HAS_CHAPTER]->(c)""",
            k=law_key,
            c=chap_key,
        )

    # Chapter ↔ Muc / Dieu
    @staticmethod
    def rel_chapter_to_node(tx, law, chap, node_title, rel):
        tx.run(
            f"""MATCH (c:Chapter {{law:$l,key:$c}}),
                      (n {{law:$l,parent:$c,title:$t}})
                MERGE (c)-[:{rel}]->(n)""",
            l=law,
            c=chap,
            t=node_title,
        )

    # Muc ↔ Tiểu mục / Điều
    @staticmethod
    def rel_muc_to_tieumuc(tx, law, chap, muc_title, tm_title, rel):
        tx.run(
            f"""MATCH (m:Muc {{law:$l,parent:$c,title:$m}}),
                      (t:TieuMuc {{law:$l,parent:$c,title:$tm}})
                MERGE (m)-[:{rel}]->(t)""",
            l=law,
            c=chap,
            m=muc_title,
            tm=tm_title,
        )

    @staticmethod
    def rel_muc_to_dieu(tx, law, chap, muc_title, dieu_title, rel):
        tx.run(
            f"""MATCH (m:Muc {{law:$l,parent:$c,title:$m}}),
                      (d:Dieu {{law:$l,parent:$c,title:$d}} )
                MERGE (m)-[:{rel}]->(d)""",
            l=law,
            c=chap,
            m=muc_title,
            d=dieu_title,
        )

    # Tiểu mục ↔ Tiểu mục / Điều
    @staticmethod
    def rel_tieumuc_to_tieumuc(tx, law, chap, parent_tm, child_tm, rel):
        tx.run(
            f"""MATCH (p:TieuMuc {{law:$l,parent:$c,title:$p}}),
                      (ch:TieuMuc {{law:$l,parent:$c,title:$ch}})
                MERGE (p)-[:{rel}]->(ch)""",
            l=law,
            c=chap,
            p=parent_tm,
            ch=child_tm,
        )

    @staticmethod
    def rel_tieumuc_to_dieu(tx, law, chap, tm_title, dieu_title, rel):
        tx.run(
            f"""MATCH (t:TieuMuc {{law:$l,parent:$c,title:$tm}}),
                      (d:Dieu {{law:$l,parent:$c,title:$d}} )
                MERGE (t)-[:{rel}]->(d)""",
            l=law,
            c=chap,
            tm=tm_title,
            d=dieu_title,
        )

    @staticmethod
    def rel_dieu_to_dieu(tx, law, article, ref_name, rel):
        tx.run(
            f"""MATCH (a:Dieu {{title:$a, law:$l}}),
                      (b:Dieu {{title:$b, law:$l}})
                MERGE (a)-[:{rel}]->(b)""",
            a=article,
            b=ref_name,
            l=law,
        )


if __name__ == "__main__":
    uri = "neo4j://18.212.177.193:7687"
    user = "neo4j"
    password = "gage-straws-number"
    json_file = "chung.json"

    imp = LawGraphImporter(uri, user, password, json_file)

    imp.import_data()
    imp.close()
