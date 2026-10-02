from app import db

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    participants = db.relationship("Participant", backref="group", lazy=True)
    expenses = db.relationship("Expense", backref="group", lazy=True)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_by_id = db.Column(db.Integer, db.ForeignKey("participant.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    shares = db.relationship("ExpenseShare", backref="expense", lazy=True)
    category = db.Column(db.String(50), nullable=False, default="General")

class ExpenseShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    expense_id = db.Column(
        db.Integer,
        db.ForeignKey("expense.id"),
        nullable=False
    )

    participant_id = db.Column(
        db.Integer,
        db.ForeignKey("participant.id"),
        nullable=False
    )

class Settlement(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    payer_id = db.Column(
        db.Integer,
        db.ForeignKey("participant.id"),
        nullable=False
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("participant.id"),
        nullable=False
    )

    amount = db.Column(db.Float, nullable=False)

    group_id = db.Column(
        db.Integer,
        db.ForeignKey("group.id"),
        nullable=False
    )