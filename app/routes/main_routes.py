from click import group
from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models.models import Group, Participant, Expense, ExpenseShare, Settlement
from app.services.settlement_service import calculate_balances

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
    participant_lookup = {participant.id: participant.name for participant in participants}
    total_spent = sum(expense.amount for expense in expenses)   
    participant_count = len(participants)
    expense_count = len(expenses)
    
    return render_template(
        "group_detail.html",
        group=group,
        participants=participants,
        expenses=expenses,
        total_spent=total_spent,
        participant_count=participant_count,
        expense_count=expense_count,
        participant_lookup=participant_lookup
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
    category = request.form.get("category")
    shared_participants = request.form.getlist("shared_participants")
    if description and amount and paid_by_id:
        expense = Expense(
            description=description,
            amount=float(amount),
            paid_by_id=int(paid_by_id),
            group_id=group_id,
            category=category
        )
        db.session.add(expense)
        db.session.commit()
        for participant_id in shared_participants:
            share = ExpenseShare(
                expense_id=expense.id,
                participant_id=int(participant_id)
            )
            db.session.add(share)
        db.session.commit()
    return redirect(url_for("main.group_detail", group_id=group_id))

@main.route("/group/<int:group_id>/settlements")
def settlements(group_id):
    group = Group.query.get_or_404(group_id)
    participants = Participant.query.filter_by(group_id=group.id).all()
    expenses = Expense.query.filter_by(group_id=group.id).all()
    participant_lookup = {participant.id: participant.name for participant in participants}
    settlement_history = Settlement.query.filter_by(group_id=group.id).all()
    balances = calculate_balances(expenses, settlement_history)

    return render_template(
        "settlements.html",
        group=group,
        balances=balances,
        participant_lookup=participant_lookup,
        settlement_history=settlement_history
    )

@main.route("/group/<int:group_id>/settle-payment", methods=["POST"])
def settle_payment(group_id):
    payer_id = request.form.get("payer_id")
    receiver_id = request.form.get("receiver_id")
    amount = request.form.get("amount")

    if payer_id and receiver_id and amount:
        settlement = Settlement(
            payer_id=int(payer_id),
            receiver_id=int(receiver_id),
            amount=float(amount),
            group_id=group_id
        )
        db.session.add(settlement)
        db.session.commit()
    return redirect(url_for("main.settlements", group_id=group_id))