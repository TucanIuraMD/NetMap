from datetime import datetime

from ..extensions import db


class Interface(db.Model):
    __tablename__ = "interfaces"

    id = db.Column(db.Integer, primary_key=True)

    device_id = db.Column(
        db.Integer,
        db.ForeignKey("devices.id"),
        nullable=False,
    )

    name = db.Column(db.String(100), nullable=False)
    mac_address = db.Column(db.String(17))
    speed = db.Column(db.Integer)
    mtu = db.Column(db.Integer)
    interface_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    device = db.relationship(
        "Device",
        back_populates="interfaces",
    )

    ip_addresses = db.relationship(
        "IPAddress",
        back_populates="interface",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Interface {self.name}>"