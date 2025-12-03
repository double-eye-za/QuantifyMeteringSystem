from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from ...models import Person, Unit, Estate, UnitOwnership, UnitTenancy
from ...services.persons import (
    list_persons as svc_list_persons,
    get_person_by_id,
    create_person as svc_create_person,
    update_person as svc_update_person,
    delete_person as svc_delete_person,
    can_person_be_deleted,
)
from ...utils.audit import log_action
from ...utils.pagination import paginate_query
from ...utils.decorators import requires_permission
from . import api_v1


@api_v1.route("/persons", methods=["GET"])
@login_required
@requires_permission("persons.view")
def persons_page():
    """Render the persons management page"""
    search = request.args.get("q") or None
    is_active = request.args.get("is_active")
    unit_id = request.args.get("unit_id", type=int)
    is_owner = request.args.get("is_owner")
    is_tenant = request.args.get("is_tenant")

    # Parse boolean filters
    if is_active == "true":
        is_active_val = True
    elif is_active == "false":
        is_active_val = False
    else:
        is_active_val = None

    if is_owner == "true":
        is_owner_val = True
    elif is_owner == "false":
        is_owner_val = False
    else:
        is_owner_val = None

    if is_tenant == "true":
        is_tenant_val = True
    elif is_tenant == "false":
        is_tenant_val = False
    else:
        is_tenant_val = None

    if not unit_id:
        unit_id = None

    # Get persons with filters
    query = svc_list_persons(
        search=search,
        is_active=is_active_val,
        unit_id=unit_id,
        is_owner=is_owner_val,
        is_tenant=is_tenant_val,
    )
    items, meta = paginate_query(query)

    # Build persons data with unit associations
    persons = []
    for person in items:
        person_data = person.to_dict()

        # Get all units this person owns
        ownerships = UnitOwnership.query.filter_by(person_id=person.id).all()
        owned_units = []
        for ownership in ownerships:
            unit = Unit.query.get(ownership.unit_id)
            if unit:
                estate = Estate.query.get(unit.estate_id)
                owned_units.append(
                    {
                        "id": unit.id,
                        "unit_number": unit.unit_number,
                        "estate_name": estate.name if estate else None,
                        "ownership_percentage": float(ownership.ownership_percentage),
                        "is_primary": ownership.is_primary_owner,
                    }
                )

        # Get all units this person rents
        tenancies = UnitTenancy.query.filter_by(person_id=person.id, status="active").all()
        rented_units = []
        for tenancy in tenancies:
            if tenancy.move_out_date:
                continue  # Skip moved-out tenancies
            unit = Unit.query.get(tenancy.unit_id)
            if unit:
                estate = Estate.query.get(unit.estate_id)
                rented_units.append(
                    {
                        "id": unit.id,
                        "unit_number": unit.unit_number,
                        "estate_name": estate.name if estate else None,
                        "is_primary": tenancy.is_primary_tenant,
                    }
                )

        person_data["owned_units"] = owned_units
        person_data["rented_units"] = rented_units
        persons.append(person_data)

    # Get all units for dropdown filters
    units = []
    for unit in (
        Unit.query.join(Estate, Unit.estate_id == Estate.id)
        .order_by(Estate.name.asc(), Unit.unit_number.asc())
        .all()
    ):
        estate = Estate.query.get(unit.estate_id)
        units.append(
            {
                "id": unit.id,
                "unit_number": unit.unit_number,
                "estate_name": estate.name if estate else "Unknown",
            }
        )

    return render_template(
        "persons/persons.html",
        persons=persons,
        units=units,
        pagination=meta,
        current_filters={
            "q": search,
            "is_active": is_active,
            "unit_id": unit_id,
            "is_owner": is_owner,
            "is_tenant": is_tenant,
        },
    )


@api_v1.get("/api/persons")
@login_required
@requires_permission("persons.view")
def list_persons():
    """API endpoint to list persons with unit associations"""
    search = request.args.get("q") or None
    is_active = request.args.get("is_active")
    is_owner = request.args.get("is_owner")
    is_tenant = request.args.get("is_tenant")
    unit_id = request.args.get("unit_id", type=int)

    # Parse boolean filters
    is_active_val = True if is_active == "true" else False if is_active == "false" else None
    is_owner_val = True if is_owner == "true" else False if is_owner == "false" else None
    is_tenant_val = True if is_tenant == "true" else False if is_tenant == "false" else None

    if not unit_id:
        unit_id = None

    query = svc_list_persons(
        search=search,
        is_active=is_active_val,
        unit_id=unit_id,
        is_owner=is_owner_val,
        is_tenant=is_tenant_val,
    )
    items, meta = paginate_query(query)

    # Build persons data with unit associations (same as page view)
    persons = []
    for person in items:
        person_data = person.to_dict()

        # Get all units this person owns
        ownerships = UnitOwnership.query.filter_by(person_id=person.id).all()
        owned_units = []
        for ownership in ownerships:
            unit = Unit.query.get(ownership.unit_id)
            if unit:
                estate = Estate.query.get(unit.estate_id)
                owned_units.append(
                    {
                        "id": unit.id,
                        "unit_number": unit.unit_number,
                        "estate_name": estate.name if estate else None,
                        "ownership_percentage": float(ownership.ownership_percentage),
                        "is_primary": ownership.is_primary_owner,
                    }
                )

        # Get all units this person rents
        tenancies = UnitTenancy.query.filter_by(person_id=person.id, status="active").all()
        rented_units = []
        for tenancy in tenancies:
            if tenancy.move_out_date:
                continue  # Skip moved-out tenancies
            unit = Unit.query.get(tenancy.unit_id)
            if unit:
                estate = Estate.query.get(unit.estate_id)
                rented_units.append(
                    {
                        "id": unit.id,
                        "unit_number": unit.unit_number,
                        "estate_name": estate.name if estate else None,
                        "is_primary": tenancy.is_primary_tenant,
                    }
                )

        person_data["owned_units"] = owned_units
        person_data["rented_units"] = rented_units
        persons.append(person_data)

    return jsonify({"data": persons, **meta})


@api_v1.post("/persons")
@login_required
@requires_permission("persons.create")
def create_person():
    """API endpoint to create a new person"""
    payload = request.get_json(force=True) or {}
    required = ["first_name", "last_name", "email", "phone"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        person = svc_create_person(payload, user_id=getattr(current_user, "id", None))
        log_action(
            "person.create", entity_type="person", entity_id=person.id, new_values=payload
        )
        return jsonify({"success": True, "id": person.id, "data": person.to_dict()}), 201

    except IntegrityError as e:
        # Handle database constraint violations with user-friendly messages
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

        if 'persons_email_key' in error_msg or ('duplicate' in error_msg and 'email' in error_msg):
            return jsonify({"error": "This email address is already registered. Please use a different email."}), 400
        elif 'persons_phone_key' in error_msg or ('duplicate' in error_msg and 'phone' in error_msg):
            return jsonify({"error": "This phone number is already registered. Please use a different phone number."}), 400
        elif 'persons_id_number_key' in error_msg or ('duplicate' in error_msg and 'id_number' in error_msg):
            return jsonify({"error": "This ID number is already registered. Please use a different ID number."}), 400
        else:
            return jsonify({"error": "A person with this information already exists. Please check your input."}), 400

    except ValueError as e:
        # Handle validation errors
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": "An unexpected error occurred. Please try again or contact support."}), 500


@api_v1.get("/persons/<int:person_id>")
@login_required
@requires_permission("persons.view")
def get_person(person_id: int):
    """API endpoint to get a single person"""
    person = get_person_by_id(person_id)
    if not person:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": person.to_dict()})


@api_v1.put("/persons/<int:person_id>")
@login_required
@requires_permission("persons.edit")
def update_person(person_id: int):
    """API endpoint to update a person"""
    person = get_person_by_id(person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    payload = request.get_json(force=True) or {}
    before = person.to_dict()

    try:
        svc_update_person(person, payload, user_id=getattr(current_user, "id", None))
        log_action(
            "person.update",
            entity_type="person",
            entity_id=person_id,
            old_values=before,
            new_values=payload,
        )
        return jsonify({"success": True, "data": person.to_dict()})

    except IntegrityError as e:
        # Handle database constraint violations with user-friendly messages
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

        if 'persons_email_key' in error_msg or ('duplicate' in error_msg and 'email' in error_msg):
            return jsonify({"error": "This email address is already registered. Please use a different email."}), 400
        elif 'persons_phone_key' in error_msg or ('duplicate' in error_msg and 'phone' in error_msg):
            return jsonify({"error": "This phone number is already registered. Please use a different phone number."}), 400
        elif 'persons_id_number_key' in error_msg or ('duplicate' in error_msg and 'id_number' in error_msg):
            return jsonify({"error": "This ID number is already registered. Please use a different ID number."}), 400
        else:
            return jsonify({"error": "A person with this information already exists. Please check your input."}), 400

    except ValueError as e:
        # Handle validation errors
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": "An unexpected error occurred. Please try again or contact support."}), 500


@api_v1.delete("/persons/<int:person_id>")
@login_required
@requires_permission("persons.delete")
def delete_person(person_id: int):
    """API endpoint to delete a person"""
    person = get_person_by_id(person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    try:
        # Check if person can be deleted
        can_delete, reason = can_person_be_deleted(person)
        if not can_delete:
            return jsonify({"error": f"Cannot delete person: {reason}"}), 409

        ok, err = svc_delete_person(person)
        if not ok:
            error_msg = err.get("message") or err.get("error") or "Failed to delete person"
            return jsonify({"error": error_msg}), 409

        log_action("person.delete", entity_type="person", entity_id=person_id)
        return jsonify({"success": True, "message": "Person deleted successfully"})

    except IntegrityError as e:
        # Handle foreign key constraint violations
        return jsonify({"error": "Cannot delete this person because they are associated with units, wallets, or other records. Please remove these associations first."}), 400

    except ValueError as e:
        # Handle validation errors
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": "An unexpected error occurred. Please try again or contact support."}), 500


@api_v1.get("/api/persons/dropdown")
@login_required
def persons_dropdown():
    """API endpoint to get persons for dropdown menus"""
    from ...services.persons import list_persons_for_dropdown

    persons = list_persons_for_dropdown()
    return jsonify(
        {
            "data": [
                {
                    "id": p.id,
                    "name": p.full_name,
                    "email": p.email,
                    "phone": p.phone,
                }
                for p in persons
            ]
        }
    )
