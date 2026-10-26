"""I75B: deterministic inventory parser and fail-closed source contracts."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "i75_g3",ROOT/"scripts/test_s1_002_i75_g3_surface_inventory.py")
scanner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)

def fixture(root,*,policies=True):
    migration=root/"supabase/migrations";migration.mkdir(parents=True)
    statements=[]
    for table,cols in scanner.CORE.items():
        statements.append("create table "+table+
            " (id uuid primary key, "+", ".join(c+" uuid" for c in cols)+");")
    (migration/"base.sql").write_text("\n".join(statements),encoding="utf-8")
    candidates=root/"supabase/tests";candidates.mkdir(parents=True)
    ps=[]
    if policies:
        for table in sorted(scanner.HISTORY):
            for tail in ("p","r"):
                ps.append("create policy s1_63_canon_"+table.split(".")[1]+
                          "_"+tail+" on "+table+" for select to authenticated using(true);")
    (candidates/"s1_087_rls_excecao_canonica_local_only.sql").write_text(
        "\n".join(ps),encoding="utf-8")

class I75BInventory(unittest.TestCase):
    def test_no_false_object_from_comments(self):
        src="-- create table public.fake(id uuid);\ncreate table public.real(id uuid);"
        self.assertEqual(scanner.ddl_columns(src),{"public.real":["id"]})

    def test_nested_column_definitions(self):
        src=("create table public.mensagens (id uuid default gen_random_uuid(),"
             "conteudo_sintetico text check(length(conteudo_sintetico)>0),"
             "concessionaria_id uuid, foreign key(id) references public.conversas(id));")
        self.assertEqual(scanner.ddl_columns(src)["public.mensagens"],
                         ["id","conteudo_sintetico","concessionaria_id"])

    def test_missing_required_tables_fails(self):
        with tempfile.TemporaryDirectory() as p:
            parent=Path(p)/"supabase/migrations";parent.mkdir(parents=True)
            (parent/"base.sql").write_text("create table public.conversas(id uuid);")
            with self.assertRaisesRegex(ValueError,"I75_REQUIRED_OBJECT_MISSING"):
                scanner.inventory(Path(p))

    def test_i63_test_policy_drift_fails(self):
        with tempfile.TemporaryDirectory() as p:
            fixture(Path(p),policies=False)
            with self.assertRaisesRegex(ValueError,"I75_I63_POLICY_BASELINE_DRIFT"):
                scanner.inventory(Path(p))

    def test_required_shop_column_drift_fails(self):
        with tempfile.TemporaryDirectory() as p:
            fixture(Path(p))
            f=Path(p)/"supabase/migrations/base.sql"
            f.write_text(f.read_text().replace(
                "concessionaria_id uuid","sem_loja uuid",1))
            with self.assertRaisesRegex(ValueError,"I75_SCOPE_KEY_DRIFT"):
                scanner.inventory(Path(p))

    def test_media_lexical_does_not_certify_access(self):
        with tempfile.TemporaryDirectory() as p:
            fixture(Path(p))
            f=Path(p)/"supabase/migrations/base.sql"
            f.write_text(f.read_text()+
                "\ncreate table prumo_private.anexos_banco(id uuid, segredo text);")
            report=scanner.inventory(Path(p))
            self.assertEqual(len(report["surfaces"]),11)
            self.assertFalse(report["media_storage_contract_verified"])
            self.assertFalse(report["d3_d4_object_column_contract_verified"])
            self.assertFalse(any(s["approved_operational_access"] for s in report["surfaces"]))
            self.assertIn("prumo_private.anexos_banco",
                {x["table"] for x in report["other_declared_tables"]})

if __name__=="__main__":unittest.main()
