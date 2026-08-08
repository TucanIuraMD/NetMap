from datetime import datetime

from ..extensions import db


class IPAddress(db.Model):
    __tablename__ = "ip_addresses"

    id = db.Column(db.Integer, primary_key=True)
    interface_id = db.Column(
        db.Integer,
        db.ForeignKey("interfaces.id"),
        nullable=False,
    )
    address = db.Column(db.String(45), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    interface = db.relationship(
        "Interface",
        back_populates="ip_addresses",
    )

    def __repr__(self) -> str:
        return f"<IPAddress {self.address}>"