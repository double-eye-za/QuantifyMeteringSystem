"""Portal profile and password routes."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...services.mobile_users import change_password, get_user_units
from ...db import db


@portal.route('/profile')
@portal_login_required
def portal_profile():
    """User profile page."""
    person = current_user.person
    units = get_user_units(current_user.person_id)

    return render_template(
        'portal/profile.html',
        person=person,
        units=units,
        mobile_user=current_user,
    )


@portal.route('/change-password', methods=['GET', 'POST'])
@portal_login_required
def portal_change_password():
    """Change password page (also used for forced password change on first login)."""
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')

        if new_pw != confirm_pw:
            flash('New passwords do not match.', 'error')
            return render_template('portal/change_password.html', force_change=current_user.password_must_change)

        # For forced change, current_password is optional
        if current_user.password_must_change:
            current_pw = None

        success, result = change_password(current_user, new_pw, current_pw)
        if success:
            flash('Password changed successfully.', 'success')
            return redirect(url_for('portal.portal_dashboard'))
        else:
            flash(result.get('message', 'Failed to change password.'), 'error')
            return render_template('portal/change_password.html', force_change=current_user.password_must_change)

    return render_template('portal/change_password.html', force_change=current_user.password_must_change)
