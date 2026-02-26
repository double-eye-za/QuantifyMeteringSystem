"""
Tests for payment role permission system (delegated_payer vs sponsored).

Covers:
- UnitTenancy model properties (effective_payment_role, can_topup, to_dict)
- can_topup_unit() service function
- get_user_units() includes can_topup field
- add_tenant() / update_tenancy() payment_role validation
"""
from __future__ import annotations

from datetime import date


# ---------------------------------------------------------------------------
# Helper: create test data for payment role scenarios
# ---------------------------------------------------------------------------

def _create_payment_role_test_data(db):
    """
    Create a test estate, two units, and three persons (Dad, Son, Tenant).

    Returns dict with all created objects for easy reference.
    """
    from app.models import Estate, Unit, Person

    estate = Estate(name="PR Test Estate")
    db.session.add(estate)
    db.session.flush()

    unit_a = Unit(estate_id=estate.id, unit_number="PR-A")
    unit_b = Unit(estate_id=estate.id, unit_number="PR-B")
    db.session.add_all([unit_a, unit_b])
    db.session.flush()

    dad = Person(
        first_name="Dad", last_name="PaymentRole",
        email="pr_dad@test.com", phone="+27810000001",
    )
    son = Person(
        first_name="Son", last_name="PaymentRole",
        email="pr_son@test.com", phone="+27810000002",
    )
    tenant = Person(
        first_name="Regular", last_name="Tenant",
        email="pr_tenant@test.com", phone="+27810000003",
    )
    db.session.add_all([dad, son, tenant])
    db.session.flush()

    return {
        "estate": estate,
        "unit_a": unit_a,
        "unit_b": unit_b,
        "dad": dad,
        "son": son,
        "tenant": tenant,
    }


# ---------------------------------------------------------------------------
# 1. UnitTenancy model property tests
# ---------------------------------------------------------------------------

def test_effective_payment_role_null_returns_delegated_payer(app):
    """NULL payment_role is treated as 'delegated_payer' for backward compat."""
    with app.app_context():
        from app.models import UnitTenancy
        t = UnitTenancy(payment_role=None)
        assert t.effective_payment_role == "delegated_payer"


def test_effective_payment_role_explicit_delegated_payer(app):
    """Explicitly set 'delegated_payer' returns 'delegated_payer'."""
    with app.app_context():
        from app.models import UnitTenancy
        t = UnitTenancy(payment_role="delegated_payer")
        assert t.effective_payment_role == "delegated_payer"


def test_effective_payment_role_sponsored(app):
    """'sponsored' returns 'sponsored'."""
    with app.app_context():
        from app.models import UnitTenancy
        t = UnitTenancy(payment_role="sponsored")
        assert t.effective_payment_role == "sponsored"


def test_can_topup_true_for_null_role(app):
    """NULL payment_role (backward compat) should allow topup."""
    with app.app_context():
        from app.models import UnitTenancy
        t = UnitTenancy(payment_role=None)
        assert t.can_topup is True


def test_can_topup_true_for_delegated_payer(app):
    """Explicit 'delegated_payer' should allow topup."""
    with app.app_context():
        from app.models import UnitTenancy
        t = UnitTenancy(payment_role="delegated_payer")
        assert t.can_topup is True


def test_can_topup_false_for_sponsored(app):
    """'sponsored' should NOT allow topup."""
    with app.app_context():
        from app.models import UnitTenancy
        t = UnitTenancy(payment_role="sponsored")
        assert t.can_topup is False


def test_to_dict_includes_payment_role_fields(app):
    """to_dict() should include payment_role, delegated_payer_id, can_topup."""
    with app.app_context():
        from app.db import db
        from app.models import UnitTenancy

        data = _create_payment_role_test_data(db)
        tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="sponsored",
            delegated_payer_id=data["dad"].id,
            status="active",
            move_in_date=date.today(),
        )
        db.session.add(tenancy)
        db.session.flush()

        d = tenancy.to_dict()
        assert d["payment_role"] == "sponsored"
        assert d["delegated_payer_id"] == data["dad"].id
        assert d["delegated_payer_name"] == "Dad PaymentRole"
        assert d["can_topup"] is False

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


# ---------------------------------------------------------------------------
# 2. can_topup_unit() service function tests
# ---------------------------------------------------------------------------

def test_can_topup_owner_always_true(app):
    """Owners can ALWAYS top up, regardless of any other configuration."""
    with app.app_context():
        from app.db import db
        from app.models import UnitOwnership
        from app.services.mobile_users import can_topup_unit

        data = _create_payment_role_test_data(db)

        # Dad owns Unit A
        ownership = UnitOwnership(
            unit_id=data["unit_a"].id,
            person_id=data["dad"].id,
            ownership_percentage=100,
        )
        db.session.add(ownership)
        db.session.flush()

        assert can_topup_unit(data["dad"].id, data["unit_a"].id) is True

        # Clean up
        db.session.delete(ownership)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_can_topup_tenant_null_role(app):
    """Tenant with NULL payment_role (pre-existing data) can top up."""
    with app.app_context():
        from app.db import db
        from app.models import UnitTenancy
        from app.services.mobile_users import can_topup_unit

        data = _create_payment_role_test_data(db)

        tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["tenant"].id,
            payment_role=None,
            status="active",
            move_in_date=date.today(),
        )
        db.session.add(tenancy)
        db.session.flush()

        assert can_topup_unit(data["tenant"].id, data["unit_b"].id) is True

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_can_topup_tenant_delegated_payer(app):
    """Tenant with explicit 'delegated_payer' role can top up."""
    with app.app_context():
        from app.db import db
        from app.models import UnitTenancy
        from app.services.mobile_users import can_topup_unit

        data = _create_payment_role_test_data(db)

        tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["dad"].id,
            payment_role="delegated_payer",
            status="active",
            move_in_date=date.today(),
        )
        db.session.add(tenancy)
        db.session.flush()

        assert can_topup_unit(data["dad"].id, data["unit_b"].id) is True

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_can_topup_tenant_sponsored_denied(app):
    """Sponsored tenant CANNOT top up."""
    with app.app_context():
        from app.db import db
        from app.models import UnitTenancy
        from app.services.mobile_users import can_topup_unit

        data = _create_payment_role_test_data(db)

        # Dad is delegated payer, Son is sponsored
        dad_tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["dad"].id,
            payment_role="delegated_payer",
            status="active",
            move_in_date=date.today(),
        )
        son_tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="sponsored",
            delegated_payer_id=data["dad"].id,
            status="active",
            move_in_date=date.today(),
        )
        db.session.add_all([dad_tenancy, son_tenancy])
        db.session.flush()

        assert can_topup_unit(data["son"].id, data["unit_b"].id) is False

        # Clean up
        db.session.delete(son_tenancy)
        db.session.delete(dad_tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_can_topup_delegated_payer_id_grants_access(app):
    """
    A person listed as delegated_payer_id on a tenancy can top up,
    even if they don't have their own tenancy for that unit.
    """
    with app.app_context():
        from app.db import db
        from app.models import UnitTenancy, Person
        from app.services.mobile_users import can_topup_unit

        data = _create_payment_role_test_data(db)

        # External payer (not a tenant themselves) — e.g. a parent paying remotely
        external_payer = Person(
            first_name="External", last_name="Payer",
            email="pr_external@test.com", phone="+27810000004",
        )
        db.session.add(external_payer)
        db.session.flush()

        # Son is a sponsored tenant; external payer is delegated payer
        son_tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="sponsored",
            delegated_payer_id=external_payer.id,
            status="active",
            move_in_date=date.today(),
        )
        db.session.add(son_tenancy)
        db.session.flush()

        # External payer can top up via delegated_payer_id reference
        assert can_topup_unit(external_payer.id, data["unit_b"].id) is True
        # Son still cannot
        assert can_topup_unit(data["son"].id, data["unit_b"].id) is False

        # Clean up
        db.session.delete(son_tenancy)
        db.session.delete(external_payer)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_can_topup_no_relationship_denied(app):
    """Person with no ownership or tenancy for a unit cannot top up."""
    with app.app_context():
        from app.db import db
        from app.services.mobile_users import can_topup_unit

        data = _create_payment_role_test_data(db)

        # Stranger has no relationship to unit_a
        assert can_topup_unit(data["son"].id, data["unit_a"].id) is False

        # Clean up
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_can_topup_terminated_tenancy_denied(app):
    """Terminated tenancies should not grant topup permission."""
    with app.app_context():
        from app.db import db
        from app.models import UnitTenancy
        from app.services.mobile_users import can_topup_unit

        data = _create_payment_role_test_data(db)

        tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["tenant"].id,
            payment_role="delegated_payer",
            status="terminated",
            move_in_date=date.today(),
        )
        db.session.add(tenancy)
        db.session.flush()

        # Terminated tenant cannot top up even with delegated_payer role
        assert can_topup_unit(data["tenant"].id, data["unit_b"].id) is False

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


# ---------------------------------------------------------------------------
# 3. get_user_units() includes can_topup field
# ---------------------------------------------------------------------------

def test_get_user_units_owner_has_can_topup_true(app):
    """Owner units returned by get_user_units() include can_topup=True."""
    with app.app_context():
        from app.db import db
        from app.models import UnitOwnership
        from app.services.mobile_users import get_user_units

        data = _create_payment_role_test_data(db)

        ownership = UnitOwnership(
            unit_id=data["unit_a"].id,
            person_id=data["dad"].id,
            ownership_percentage=100,
        )
        db.session.add(ownership)
        db.session.flush()

        units = get_user_units(data["dad"].id)
        owner_units = [u for u in units if u["role"] == "owner"]
        assert len(owner_units) == 1
        assert owner_units[0]["can_topup"] is True

        # Clean up
        db.session.delete(ownership)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_get_user_units_delegated_payer_has_can_topup_true(app):
    """Delegated payer tenant has can_topup=True in get_user_units()."""
    with app.app_context():
        from app.db import db
        from app.models import UnitTenancy
        from app.services.mobile_users import get_user_units

        data = _create_payment_role_test_data(db)

        tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["dad"].id,
            payment_role="delegated_payer",
            status="active",
            move_in_date=date.today(),
        )
        db.session.add(tenancy)
        db.session.flush()

        units = get_user_units(data["dad"].id)
        tenant_units = [u for u in units if u["role"] == "tenant"]
        assert len(tenant_units) == 1
        assert tenant_units[0]["can_topup"] is True
        assert tenant_units[0]["payment_role"] == "delegated_payer"

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_get_user_units_sponsored_has_can_topup_false(app):
    """Sponsored tenant has can_topup=False in get_user_units()."""
    with app.app_context():
        from app.db import db
        from app.models import UnitTenancy
        from app.services.mobile_users import get_user_units

        data = _create_payment_role_test_data(db)

        tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="sponsored",
            delegated_payer_id=data["dad"].id,
            status="active",
            move_in_date=date.today(),
        )
        db.session.add(tenancy)
        db.session.flush()

        units = get_user_units(data["son"].id)
        tenant_units = [u for u in units if u["role"] == "tenant"]
        assert len(tenant_units) == 1
        assert tenant_units[0]["can_topup"] is False
        assert tenant_units[0]["payment_role"] == "sponsored"

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


# ---------------------------------------------------------------------------
# 4. add_tenant() service validation
# ---------------------------------------------------------------------------

def test_add_tenant_sponsored_without_payer_rejected(app):
    """Adding a sponsored tenant without delegated_payer_id must fail."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant

        data = _create_payment_role_test_data(db)

        success, result = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="sponsored",
            delegated_payer_id=None,
        )

        assert success is False
        assert result["code"] == 400
        assert "delegated payer" in result["message"].lower()

        # Clean up
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_add_tenant_sponsored_with_payer_accepted(app):
    """Adding a sponsored tenant with valid delegated_payer_id succeeds."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant

        data = _create_payment_role_test_data(db)

        success, tenancy = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="sponsored",
            delegated_payer_id=data["dad"].id,
        )

        assert success is True
        assert tenancy.payment_role == "sponsored"
        assert tenancy.delegated_payer_id == data["dad"].id
        assert tenancy.can_topup is False

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_add_tenant_no_role_backward_compat(app):
    """Adding a tenant without specifying payment_role works (backward compat)."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant

        data = _create_payment_role_test_data(db)

        success, tenancy = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["tenant"].id,
        )

        assert success is True
        # payment_role should be None (which is treated as 'delegated_payer')
        assert tenancy.effective_payment_role == "delegated_payer"
        assert tenancy.can_topup is True

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_add_tenant_invalid_payment_role_rejected(app):
    """Invalid payment_role value must be rejected."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant

        data = _create_payment_role_test_data(db)

        success, result = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="admin_payer",  # invalid
        )

        assert success is False
        assert result["code"] == 400
        assert "payment_role" in result["message"].lower()

        # Clean up
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_add_tenant_invalid_payer_id_rejected(app):
    """delegated_payer_id referencing a non-existent person must fail."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant

        data = _create_payment_role_test_data(db)

        success, result = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="sponsored",
            delegated_payer_id=999999,  # non-existent person
        )

        assert success is False
        assert result["code"] == 404
        assert "payer" in result["message"].lower()

        # Clean up
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_add_tenant_delegated_payer_explicit(app):
    """Explicit 'delegated_payer' role works correctly."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant

        data = _create_payment_role_test_data(db)

        success, tenancy = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["dad"].id,
            payment_role="delegated_payer",
        )

        assert success is True
        assert tenancy.payment_role == "delegated_payer"
        assert tenancy.can_topup is True

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


# ---------------------------------------------------------------------------
# 5. update_tenancy() service validation
# ---------------------------------------------------------------------------

def test_update_tenancy_change_role_to_sponsored(app):
    """Can update a tenant from delegated_payer to sponsored."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant, update_tenancy

        data = _create_payment_role_test_data(db)

        # First add as delegated payer
        success, tenancy = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="delegated_payer",
        )
        assert success is True
        assert tenancy.can_topup is True

        # Update to sponsored with a payer
        success, updated = update_tenancy(
            tenancy,
            payment_role="sponsored",
            delegated_payer_id=data["dad"].id,
        )
        assert success is True
        assert updated.payment_role == "sponsored"
        assert updated.delegated_payer_id == data["dad"].id
        assert updated.can_topup is False

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_update_tenancy_sponsored_without_payer_rejected(app):
    """Cannot update to sponsored without a delegated payer."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant, update_tenancy

        data = _create_payment_role_test_data(db)

        success, tenancy = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="delegated_payer",
        )
        assert success is True

        # Try updating to sponsored without payer
        success, result = update_tenancy(
            tenancy,
            payment_role="sponsored",
        )
        assert success is False
        assert result["code"] == 400
        assert "delegated payer" in result["message"].lower()

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


def test_update_tenancy_invalid_role_rejected(app):
    """Invalid payment_role on update is rejected."""
    with app.app_context():
        from app.db import db
        from app.services.unit_tenancies import add_tenant, update_tenancy

        data = _create_payment_role_test_data(db)

        success, tenancy = add_tenant(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
        )
        assert success is True

        success, result = update_tenancy(
            tenancy,
            payment_role="vip_payer",
        )
        assert success is False
        assert result["code"] == 400

        # Clean up
        db.session.delete(tenancy)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()


# ---------------------------------------------------------------------------
# 6. Full scenario: Dad + Son real-world flow
# ---------------------------------------------------------------------------

def test_full_scenario_dad_and_son(app):
    """
    Real-world scenario:
    - Dad owns Unit A (his house)
    - Dad is delegated_payer tenant on Unit B (son's flat)
    - Son is sponsored tenant on Unit B
    - Dad can topup both A and B
    - Son can view B but NOT topup
    """
    with app.app_context():
        from app.db import db
        from app.models import UnitOwnership, UnitTenancy
        from app.services.mobile_users import can_topup_unit, get_user_units

        data = _create_payment_role_test_data(db)

        # Dad owns Unit A
        ownership = UnitOwnership(
            unit_id=data["unit_a"].id,
            person_id=data["dad"].id,
            ownership_percentage=100,
            is_primary_owner=True,
        )
        db.session.add(ownership)
        db.session.flush()

        # Dad is delegated_payer tenant on Unit B
        dad_tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["dad"].id,
            payment_role="delegated_payer",
            is_primary_tenant=True,
            status="active",
            move_in_date=date.today(),
        )
        # Son is sponsored tenant on Unit B
        son_tenancy = UnitTenancy(
            unit_id=data["unit_b"].id,
            person_id=data["son"].id,
            payment_role="sponsored",
            delegated_payer_id=data["dad"].id,
            status="active",
            move_in_date=date.today(),
        )
        db.session.add_all([dad_tenancy, son_tenancy])
        db.session.flush()

        # --- Permission checks ---

        # Dad can topup Unit A (owner)
        assert can_topup_unit(data["dad"].id, data["unit_a"].id) is True
        # Dad can topup Unit B (delegated_payer tenant)
        assert can_topup_unit(data["dad"].id, data["unit_b"].id) is True

        # Son CANNOT topup Unit A (no relationship)
        assert can_topup_unit(data["son"].id, data["unit_a"].id) is False
        # Son CANNOT topup Unit B (sponsored)
        assert can_topup_unit(data["son"].id, data["unit_b"].id) is False

        # --- get_user_units checks ---

        dad_units = get_user_units(data["dad"].id)
        assert len(dad_units) == 2
        dad_owner_units = [u for u in dad_units if u["role"] == "owner"]
        dad_tenant_units = [u for u in dad_units if u["role"] == "tenant"]
        assert len(dad_owner_units) == 1
        assert dad_owner_units[0]["can_topup"] is True
        assert len(dad_tenant_units) == 1
        assert dad_tenant_units[0]["can_topup"] is True

        son_units = get_user_units(data["son"].id)
        assert len(son_units) == 1
        assert son_units[0]["role"] == "tenant"
        assert son_units[0]["can_topup"] is False
        assert son_units[0]["payment_role"] == "sponsored"

        # Clean up
        db.session.delete(son_tenancy)
        db.session.delete(dad_tenancy)
        db.session.delete(ownership)
        for obj in [data["dad"], data["son"], data["tenant"]]:
            db.session.delete(obj)
        for obj in [data["unit_a"], data["unit_b"]]:
            db.session.delete(obj)
        db.session.delete(data["estate"])
        db.session.commit()
