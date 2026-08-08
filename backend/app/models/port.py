from datetime import datetime

from ..extensions import db


class Port(db.Model):
    __tablename__ = "ports"

    id = db.Column(db.Integer, primary_key=True)

    device_id = db.Column(
        db.Integer,
        db.ForeignKey("devices.id"),
        nullable=False,
    )
    service_id = db.Column(
        db.Integer,
        db.ForeignKey("services.id"),
        nullable=True,
    )
    
    port_number = db.Column(db.Integer, nullable=False)
    protocol = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")
    description = db.Column(db.Text)

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
        back_populates="ports",
    )
    service = db.relationship(
        "Service",
        back_populates="ports",
    )
    
    def __repr__(self) -> str:
        return f"<Port {self.port_number}/{self.protocol}>"
