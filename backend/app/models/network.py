from datetime import datetime

from ..extensions import db


class Network(db.Model):
    __tablename__ = "networks"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(
        db.Integer,
        db.ForeignKey("sites.id"),
        nullable=False,
    )
    name = db.Column(db.String(100), nullable=False)
    cidr = db.Column(db.String(43), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    site = db.relationship(
        "Site",
        backref=db.backref("networks", lazy=True),
    )

    def __repr__(self) -> str:
        return f"<Network {self.name}>"