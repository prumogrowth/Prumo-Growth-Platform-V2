"""S0/S1 CFI-01 strict local authorization tests; no actual PostgreSQL connection."""
import unittest
from backend.identity_boundary import Principal
from backend.s0_human_closure_event_local import S1Proof, ClosureState
from backend.s0_s1_closure_authority_local import (
    S0S1LocalTeamAuthority, _TEAM_FIRST, _SCOPE,
)
from backend.tests.test_s0_human_closure_event_local import (
    A, S, SHOP, C, ASSIGN, execute, Cursor, _CASE,
)


class S1Cursor:
    def __init__(self, team=True, scope=True):
        self.team=team;self.scope=scope;self.calls=[];self.next=None
    def execute(self,sql,params):
        self.calls.append((sql,params))
        self.next=(A,) if sql==_TEAM_FIRST and self.team else ((1,) if sql==_SCOPE and self.scope else None)
    def fetchone(self):return self.next


class S1ContractTests(unittest.TestCase):
    def test_01_active_team_has_preliminary_allow(self):
        c=S1Cursor();self.assertIs(S0S1LocalTeamAuthority().lock_team(c,Principal(A,S)),S1Proof.ALLOW)
    def test_02_absent_team_denies(self):
        c=S1Cursor(team=False);self.assertIs(S0S1LocalTeamAuthority().lock_team(c,Principal(A,S)),S1Proof.DENY)
    def test_03_team_query_requires_active_and_lock(self):
        self.assertIn("e.estado='ativo'",_TEAM_FIRST)
        self.assertIn('for share of e',_TEAM_FIRST)
    def test_04_scope_matching_assignment_allowed(self):
        c=S1Cursor();self.assertIs(S0S1LocalTeamAuthority().check(c,Principal(A,S),SHOP,C,ASSIGN),S1Proof.ALLOW)
    def test_05_revoked_or_missing_scope_denies(self):
        c=S1Cursor(scope=False);self.assertIs(S0S1LocalTeamAuthority().check(c,Principal(A,S),SHOP,C,ASSIGN),S1Proof.DENY)
    def test_06_scope_params_cannot_be_provided_by_browser(self):
        c=S1Cursor();S0S1LocalTeamAuthority().check(c,Principal(A,S),SHOP,C,ASSIGN)
        self.assertEqual(c.calls[-1][1],(ASSIGN,A,SHOP,C))
    def test_07_scope_query_prevents_cross_store(self):
        self.assertIn('a.concessionaria_id=%s::uuid',_SCOPE)
        self.assertIn('a.caso_id=%s::uuid',_SCOPE)
        self.assertIn('a.encerrada_em is null',_SCOPE)
    def test_08_scope_query_rechecks_grant(self):
        self.assertIn('public.vinculos_papel_escopo',_SCOPE)
        self.assertIn("v.papel in ('operador','gestor')",_SCOPE)
        self.assertIn('v.valido_ate',_SCOPE)
    def test_09_scope_requires_uuid_not_text(self):
        c=S1Cursor()
        self.assertIs(S0S1LocalTeamAuthority().check(c,Principal(A,S),str(SHOP),C,ASSIGN),S1Proof.DENY)
        self.assertEqual(c.calls,[])
    def test_10_team_requires_valid_principal(self):
        c=S1Cursor()
        self.assertIs(S0S1LocalTeamAuthority().lock_team(c,'fake'),S1Proof.DENY)
        self.assertEqual(c.calls,[])
    def test_11_scope_requires_valid_principal(self):
        c=S1Cursor()
        self.assertIs(S0S1LocalTeamAuthority().check(c,'fake',SHOP,C,ASSIGN),S1Proof.DENY)
        self.assertEqual(c.calls,[])
    def test_12_read_queries_have_no_mutation(self):
        for sql in (_TEAM_FIRST,_SCOPE):
            self.assertTrue(sql.lstrip().lower().startswith('select'))
            for forbidden in ('update public.', 'insert into', 'delete from', 'drop table'):
                self.assertNotIn(forbidden,sql.lower())
    def test_13_s1_table_missing_fails_closed_on_capture(self):
        class UndefinedS1(S0S1LocalTeamAuthority):
            def lock_team(self,cursor,principal):
                raise RuntimeError('relation public.equipe_prumo_s1 does not exist')
        result,cursor,*_=execute(s1=UndefinedS1())
        self.assertIs(result.state,ClosureState.UNAVAILABLE)
        self.assertNotIn(_CASE,[query for query,params in cursor.calls])
    def test_14_no_case_exception_accepted_by_normal_adapter(self):
        self.assertNotIn('s1_excecoes_55',_SCOPE)
        self.assertNotIn('s1_excecoes_55',_TEAM_FIRST)
    def test_15_team_check_binds_verified_actor(self):
        c=S1Cursor();S0S1LocalTeamAuthority().lock_team(c,Principal(A,S))
        self.assertEqual(c.calls[0][1],(A,))
    def test_16_scope_locked_to_current_assignment(self):
        self.assertIn('a.id=%s::uuid',_SCOPE)
        self.assertIn('a.operador_id=%s::uuid',_SCOPE)

    def test_17_actual_s1_adapter_inside_closure_cursor(self):
        class IntegratedCursor(Cursor):
            def execute(self,sql,params):
                if sql in (_TEAM_FIRST,_SCOPE):
                    self.calls.append((sql,params))
                    self.next=(1,)
                else: super().execute(sql,params)
        c=IntegratedCursor()
        result,c,*_=execute(cursor=c,s1=S0S1LocalTeamAuthority())
        self.assertIs(result.state,ClosureState.CAPTURED_LOCAL_ONLY)
        statements=[q for q,_ in c.calls]
        self.assertLess(statements.index(_TEAM_FIRST),statements.index(_CASE))
        self.assertLess(statements.index(_CASE),statements.index(_SCOPE))

    def test_18_inactive_team_rejects_before_case_in_full_route(self):
        class InactiveCursor(Cursor):
            def execute(self,sql,params):
                if sql==_TEAM_FIRST:
                    self.calls.append((sql,params));self.next=None
                else: super().execute(sql,params)
        c=InactiveCursor()
        result,c,*_=execute(cursor=c,s1=S0S1LocalTeamAuthority())
        self.assertIs(result.state,ClosureState.BLOCKED_S1)
        self.assertNotIn(_CASE,[q for q,_ in c.calls])

    def test_19_lost_scope_rejects_before_messages_in_full_route(self):
        class RevokedCursor(Cursor):
            def execute(self,sql,params):
                if sql in (_TEAM_FIRST,_SCOPE):
                    self.calls.append((sql,params));self.next=(1,) if sql==_TEAM_FIRST else None
                else: super().execute(sql,params)
        c=RevokedCursor()
        result,c,*_=execute(cursor=c,s1=S0S1LocalTeamAuthority())
        self.assertIs(result.state,ClosureState.BLOCKED_S1)
        self.assertNotIn('select m.id',[q[:11] for q,_ in c.calls])

    def test_20_missing_s1_schema_rejects_full_route(self):
        class MissingSchemaCursor(Cursor):
            def execute(self,sql,params):
                if sql==_TEAM_FIRST:raise RuntimeError('S1 migration not installed')
                return super().execute(sql,params)
        result,c,*_=execute(cursor=MissingSchemaCursor(),s1=S0S1LocalTeamAuthority())
        self.assertIs(result.state,ClosureState.UNAVAILABLE)

if __name__=='__main__':unittest.main()
