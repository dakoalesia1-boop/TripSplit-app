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

@main.route("/group/<int:group_id>/add-participant", methods=["POST"])
def add_participant(group_id):
    participant_name = request.form.get("participant_name")
    if participant_name:
        participant = Participant(
            name=participant_name,
            group_id=group_id
        )
        db.session.add(participant)
        db.session.commit()
    return redirect(url_for("main.group_detail", group_id=group_id))

@main.route("/group/<int:group_id>/add-expense", methods=["POST"])
def add_expense(group_id):
    description = request.form.get("description")
    amount = request.form.get("amount")
    paid_by_id = request.form.get("paid_by_id")
    if description and amount and paid_by_id:
        expense = Expense(
            description=description,
            amount=float(amount),
            paid_by_id=int(paid_by_id),
            group_id=group_id
        )
        db.session.add(expense)
        db.session.commit()
    return redirect(url_for("main.group_detail", group_id=group_id))