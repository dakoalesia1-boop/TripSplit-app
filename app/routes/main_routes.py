from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.models import Group, Participant, Expense

main = Blueprint("main", __name__)
@main.route("/")
def home():
    groups = Group.query.all()
    return render_template("index.html", groups=groups)


@main.route("/create-group", methods=["POST"])
def create_group():
    group_name = request.form.get("group_name")
    if group_name:
        new_group = Group(name=group_name)
        db.session.add(new_group)
        db.session.commit()
    return redirect(url_for("main.home"))

@main.route("/group/<int:group_id>")
def group_detail(group_id):
    group = Group.query.get_or_404(group_id)
    participants = Participant.query.filter_by(group_id=group.id).all()
    expenses = Expense.query.filter_by(group_id=group.id).all()
    return render_template(
        "group_detail.html",
        group=group,
        participants=participants,
        expenses=expenses
    )