"""
build_prototype_kg.py — สร้างต้นแบบ Knowledge Graph จากข้อมูลที่มีอยู่แล้วใน SQLite
(instructors, nu_forms, courses) ใช้ NetworkX (เบา ไม่ต้องติดตั้ง graph database แยก)
เหมาะทำต้นแบบทดสอบก่อนตัดสินใจลงทุน Neo4j จริง

ตรวจสอบสคีมาปัจจุบันแล้ว (src/database/sqlite_db.py) พบข้อจำกัดสำคัญ 2 จุด
ที่ต้องบอกตรง ๆ ก่อนใช้ไฟล์นี้:

  1. ตาราง courses ในฐานข้อมูลจริงตอนนี้ "ยังไม่มีข้อมูล" (0 rows ตอนที่เช็ค) —
     โค้ดด้านล่างที่ดึงจาก courses จะรันได้แต่ได้กราฟว่างเปล่าจนกว่าจะกรอกข้อมูลจริง
  2. ไม่มีข้อมูลเชื่อม "อาจารย์คนไหนสอนวิชาไหน" เพราะฉะนั้นคำถามตัวอย่างแบบ
     "อาจารย์ที่สอนวิชา X อยู่ห้องไหน" ในรายงานยังทำ multi-hop จริงไม่ได้กับข้อมูล
     ปัจจุบัน — ตาราง course_instructors "มีอยู่แล้ว" ใน src/database/sqlite_db.py
     (schema: id, course_code, instructor_id FK→instructors(id), semester,
     academic_year, role) พร้อมฟังก์ชัน add_teaching_assignment(course_code,
     instructor_name, ...) ให้กรอกข้อมูลจริงได้เลย ไม่ต้องสร้างตารางเพิ่มในไฟล์นี้

     (แก้ 2026-07-17: ไฟล์นี้เคยมีฟังก์ชัน add_teaching_assignments_table() ที่สร้าง
     ตาราง course_instructors ชื่อซ้ำกับของ sqlite_db.py แต่ schema ต่างกัน (คอลัมน์
     instructor_name TEXT แทน instructor_id) — ลบออกแล้ว เพราะ CREATE TABLE
     IF NOT EXISTS จะ no-op เงียบ ๆ ถ้าตารางจริงถูกสร้างโดย sqlite_db.py ไปก่อนแล้ว
     (กรณีปกติ เพราะแอปเรียก init_database() ตอน startup) ทำให้ตัวอย่าง INSERT ที่
     เคยแนะนำไว้ error จริงเพราะคอลัมน์ไม่ตรงกับตารางจริง ใช้ add_teaching_assignment()
     จาก sqlite_db.py เป็นทางเดียวในการกรอกข้อมูลนี้แทน)

กราฟที่ "สร้างได้จริงวันนี้" โดยไม่ต้องกรอกข้อมูลเพิ่ม (instructors + nu_forms มีข้อมูลจริงแล้ว):

    instructor --สังกัด--> department
    nu_form    --อยู่ในหมวด--> category

ใช้ตอบคำถามเชิงโครงสร้าง (aggregate/filter) ได้แม่นกว่า vector search ล้วน ๆ เช่น
"มีฟอร์มอะไรบ้างในหมวดลงทะเบียน" (ต้องรวมหลายแถวมาตอบ ซึ่ง vector top-k เดี่ยว ๆ
มักตอบไม่ครบ เพราะแต่ละฟอร์มอยู่คนละ chunk)
"""

import sqlite3
import networkx as nx

from src.config import SQLITE_PATH


def build_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row

    for row in conn.execute("SELECT name, title_short, department FROM instructors"):
        inst_node = f"instructor:{row['name']}"
        dept_node = f"department:{row['department']}"
        g.add_node(inst_node, type="instructor", title_short=row["title_short"])
        g.add_node(dept_node, type="department")
        g.add_edge(inst_node, dept_node, relation="สังกัด")

    for row in conn.execute("SELECT code, name_th, category FROM nu_forms"):
        form_node = f"form:{row['code']}"
        g.add_node(form_node, type="form", name_th=row["name_th"])
        if row["category"]:
            category_node = f"category:{row['category']}"
            g.add_node(category_node, type="category")
            g.add_edge(form_node, category_node, relation="อยู่ในหมวด")

    for row in conn.execute("SELECT code, name_th, program, category FROM courses"):
        course_node = f"course:{row['code']}"
        g.add_node(course_node, type="course", name_th=row["name_th"])
        if row["program"]:
            program_node = f"program:{row['program']}"
            g.add_node(program_node, type="program")
            g.add_edge(course_node, program_node, relation="อยู่ในหลักสูตร")
        if row["category"]:
            category_node = f"category:{row['category']}"
            g.add_node(category_node, type="category")
            g.add_edge(course_node, category_node, relation="อยู่ในหมวด")

    conn.close()
    return g


def forms_in_category(g: nx.DiGraph, category: str) -> list[str]:
    category_node = f"category:{category}"
    if category_node not in g:
        return []
    form_nodes = [u for u, v, d in g.in_edges(category_node, data=True) if d.get("relation") == "อยู่ในหมวด" and u.startswith("form:")]
    return [g.nodes[f].get("name_th", f) for f in form_nodes]


def courses_in_program_category(g: nx.DiGraph, program: str, category: str) -> list[str]:
    program_node = f"program:{program}"
    category_node = f"category:{category}"
    if program_node not in g or category_node not in g:
        return []
    in_program = {u for u, v in g.in_edges(program_node)}
    in_category = {u for u, v in g.in_edges(category_node)}
    matched = in_program & in_category
    return [g.nodes[c].get("name_th", c) for c in matched]


def teach_course_lookup_example():
    pass

if __name__ == "__main__":
    graph = build_graph()
    print(f" สร้างกราฟสำเร็จ: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    print("\nตัวอย่าง query ที่ใช้ได้กับข้อมูลจริงวันนี้ — ฟอร์มในหมวด 'ทั่วไป':")
    print(forms_in_category(graph, "ทั่วไป"))

    n_courses = sum(1 for n, d in graph.nodes(data=True) if d.get("type") == "course")
    if n_courses == 0:
        print("\n  ตาราง courses ยังไม่มีข้อมูล — courses_in_program_category() จะคืน [] เสมอ")
        print("   จนกว่าจะกรอกข้อมูลจริงเข้าตาราง courses ก่อน")